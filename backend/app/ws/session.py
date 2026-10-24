"""WebSocket session gateway endpoint, connection manager, and audio frame ingest."""

from __future__ import annotations

import base64
import json
import logging
import struct
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel

from app.contracts.events_v1 import (
    AudioChunkEvent,
    CustomerContextPayload,
    EventRole,
    SessionEndEvent,
    SessionJoinEvent,
    SessionReadyEvent,
    TranscriptManualEvent,
)
from app.core.security import SecurityError, TokenPayload, get_security_manager
from app.ports.event_bus import EventBus
from app.services.transcription import TranscriptionService
from app.ws.fanout import OutboundEventFilter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


class SessionConnectionManager:
    """Manages active WebSocket connections per session with role isolation."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        # session_id -> {participant_id: (websocket, role)}
        self._sessions: dict[str, dict[str, tuple[WebSocket, str]]] = {}
        self.event_bus = event_bus

    def register(
        self, session_id: str, participant_id: str, role: str, websocket: WebSocket
    ) -> None:
        if session_id not in self._sessions:
            self._sessions[session_id] = {}
        self._sessions[session_id][participant_id] = (websocket, role)
        logger.info("Participant %s (%s) joined session %s", participant_id, role, session_id)

    def remove(self, session_id: str, participant_id: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id].pop(participant_id, None)
            if not self._sessions[session_id]:
                self._sessions.pop(session_id, None)
        logger.info("Participant %s removed from session %s", participant_id, session_id)

    def get_participants(self, session_id: str) -> dict[str, tuple[WebSocket, str]]:
        return self._sessions.get(session_id, {})

    async def broadcast(self, session_id: str, event: dict[str, Any] | BaseModel) -> None:
        """Broadcast event to all session participants applying role-based isolation."""
        participants = self.get_participants(session_id)
        if not participants:
            return

        raw_event = event.model_dump(mode="json") if isinstance(event, BaseModel) else dict(event)

        # Publish to distributed event bus if available
        if self.event_bus is not None:
            try:
                await self.event_bus.publish(f"session:{session_id}:events", raw_event)
            except Exception as e:
                logger.debug("Event bus publish error: %s", e)

        # Deliver to local WebSockets with role filtering
        disconnected: list[str] = []
        for p_id, (ws, role) in participants.items():
            filtered = OutboundEventFilter.filter_event_for_role(raw_event, role)
            if filtered is None:
                continue  # Suppressed for this role (e.g. assist data to customer)

            try:
                await ws.send_text(json.dumps(filtered))
            except Exception:
                disconnected.append(p_id)

        for p_id in disconnected:
            self.remove(session_id, p_id)


_global_manager: SessionConnectionManager | None = None


def get_connection_manager() -> SessionConnectionManager:
    global _global_manager
    if _global_manager is None:
        _global_manager = SessionConnectionManager()
    return _global_manager


@router.post("/api/v1/sessions/token")
async def create_session_join_token(
    session_id: str,
    role: str = "customer",
    participant_id: str | None = None,
) -> dict[str, Any]:
    """Issue signed HMAC/JWT join token for WebSocket authentication."""
    sec = get_security_manager()
    p_id = participant_id or f"{role}_{session_id[-6:]}"
    role_literal = "customer" if role.lower() == "customer" else "agent"
    token = sec.create_join_token(session_id=session_id, participant_id=p_id, role=role_literal)
    return {
        "session_id": session_id,
        "participant_id": p_id,
        "role": role_literal,
        "token": token,
        "ttl_seconds": sec.default_ttl,
    }


@router.websocket("/ws/session/{session_id}")
async def session_websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str | None = Query(default=None),
    role: str = Query(default="customer"),
    participant_id: str | None = Query(default=None),
) -> None:
    """Real-time bi-directional voice and control channel."""
    sec = get_security_manager()
    manager = get_connection_manager()

    p_id = participant_id or f"{role}_{session_id[-4:]}"
    validated_role = role

    # Authenticate token if provided
    if token:
        try:
            token_payload: TokenPayload = await sec.verify_join_token(
                token=token,
                expected_session_id=session_id,
                check_single_use=True,
            )
            validated_role = token_payload.role
            p_id = token_payload.sub
        except SecurityError as e:
            logger.warning("WebSocket authentication rejected for session %s: %s", session_id, e)
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(e))
            return

    await websocket.accept()
    manager.register(session_id, p_id, validated_role, websocket)

    # Instantiate transcription service callback linked to broadcast
    async def _on_event(evt: Any) -> None:
        await manager.broadcast(session_id, evt)

    # In local/test mode, use LocalFasterWhisperSTT
    from app.adapters.local.whisper_stt import LocalFasterWhisperSTT

    stt_adapter = LocalFasterWhisperSTT()
    transcription_service = TranscriptionService(
        stt_adapter=stt_adapter,
        event_callback=_on_event,
    )

    # Emit SessionReadyEvent
    ready_evt = SessionReadyEvent(
        session_id=session_id,
        participant_id=p_id,
        role=EventRole(validated_role),
        status="connected",
        customer_context=CustomerContextPayload(
            customer_id="cust_sarah_jenkins_01",
            name="Sarah Jenkins",
            account_type="Sapphire Preferred Visa Signature",
            relationship_tier="Platinum",
            account_number_masked="•••• 4821",
            context_summary="Customer overseas (Paris). Automated security hold triggered.",
        ),
    )
    # Deliver ready event to this connection
    await websocket.send_text(json.dumps(ready_evt.model_dump(mode="json")))

    try:
        while True:
            message = await websocket.receive()

            # Handle text message
            if "text" in message and message["text"]:
                try:
                    raw_data = json.loads(message["text"])
                    evt_type = raw_data.get("type", "")

                    if evt_type == "session.join":
                        join_evt = SessionJoinEvent.model_validate(raw_data)
                        logger.debug("Received session.join from %s", join_evt.participant_id)

                    elif evt_type == "transcript.manual":
                        manual_evt = TranscriptManualEvent.model_validate(raw_data)
                        await transcription_service.handle_manual_transcript(manual_evt)

                    elif evt_type == "audio.chunk":
                        chunk_evt = AudioChunkEvent.model_validate(raw_data)
                        raw_pcm = (
                            base64.b64decode(chunk_evt.payload_base64)
                            if chunk_evt.payload_base64
                            else b""
                        )
                        if raw_pcm:
                            await transcription_service.handle_audio_chunk(chunk_evt, raw_pcm)

                    elif evt_type == "session.end":
                        end_evt = SessionEndEvent.model_validate(raw_data)
                        await manager.broadcast(session_id, end_evt)
                        break

                except Exception as e:
                    logger.debug("Error processing text WS message: %s", e)

            # Handle binary audio chunk
            elif "bytes" in message and message["bytes"]:
                raw_bytes = message["bytes"]
                # Check for binary header: magic 0xCC 0x01 | uint32 seq | uint8 role
                seq = 0
                pcm_data = raw_bytes
                if len(raw_bytes) > 7 and raw_bytes[:2] == b"\xcc\x01":
                    seq = struct.unpack(">I", raw_bytes[2:6])[0]
                    pcm_data = raw_bytes[7:]

                audio_evt = AudioChunkEvent(
                    session_id=session_id,
                    participant_id=p_id,
                    role=EventRole(validated_role),
                    seq=seq,
                )
                await transcription_service.handle_audio_chunk(audio_evt, pcm_data)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s in session %s", p_id, session_id)
    finally:
        manager.remove(session_id, p_id)
