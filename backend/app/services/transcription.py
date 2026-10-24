"""Real-time transcription service coordinating audio chunk buffering, STT, and utterance finalization."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

from app.contracts.events_v1 import (
    AudioChunkEvent,
    EventRole,
    TranscriptFinalEvent,
    TranscriptManualEvent,
    TranscriptPartialEvent,
)
from app.ports.speech_to_text import SpeechToText
from app.services.realtime_orchestrator import RealtimeOrchestrator

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Coordinates audio frame ingestion, sequence ordering, speech-to-text decoding, and turn triggers."""

    def __init__(
        self,
        stt_adapter: SpeechToText,
        orchestrator: RealtimeOrchestrator | None = None,
        event_callback: Callable[[Any], Any] | None = None,
    ) -> None:
        self.stt = stt_adapter
        self.orchestrator = orchestrator
        self.event_callback = event_callback

        # Track session turn counter and packet sequence tracking
        self._turn_counters: dict[str, int] = {}
        self._last_seq_by_participant: dict[str, int] = {}
        self._active_utterance_start: dict[str, float] = {}

    def _next_turn_id(self, session_id: str) -> int:
        count = self._turn_counters.get(session_id, 0) + 1
        self._turn_counters[session_id] = count
        return count

    async def _emit_event(self, event: Any) -> None:
        if self.event_callback is not None:
            res = self.event_callback(event)
            if asyncio.iscoroutine(res):
                await res

    async def handle_audio_chunk(
        self,
        event: AudioChunkEvent,
        raw_pcm: bytes,
    ) -> None:
        """Process incoming 16kHz mono linear PCM audio chunk."""
        participant_key = f"{event.session_id}:{event.participant_id}"

        # Sequence gap check (resilience against packet drop)
        last_seq = self._last_seq_by_participant.get(participant_key, -1)
        if last_seq >= 0 and event.seq > last_seq + 1:
            gap = event.seq - (last_seq + 1)
            logger.debug(
                "Audio packet sequence gap detected for %s: %d packet(s) dropped (expected %d, got %d)",
                participant_key,
                gap,
                last_seq + 1,
                event.seq,
            )
        self._last_seq_by_participant[participant_key] = event.seq

        if participant_key not in self._active_utterance_start:
            self._active_utterance_start[participant_key] = time.time()

        # Transcribe chunk
        text = await self.stt.transcribe_chunk(raw_pcm, is_final=False)
        if text:
            turn_id = self._turn_counters.get(event.session_id, 1)
            partial_event = TranscriptPartialEvent(
                session_id=event.session_id,
                turn_id=turn_id,
                speaker=event.role,
                text=text,
            )
            await self._emit_event(partial_event)

    async def finalize_utterance(
        self,
        session_id: str,
        participant_id: str,
        role: EventRole,
        final_text: str,
    ) -> TranscriptFinalEvent:
        """Mark end of speech utterance and trigger downstream orchestrator."""
        participant_key = f"{session_id}:{participant_id}"
        start_time = self._active_utterance_start.pop(participant_key, time.time())
        duration_ms = max(100.0, (time.time() - start_time) * 1000.0)

        turn_id = self._next_turn_id(session_id)
        final_event = TranscriptFinalEvent(
            session_id=session_id,
            turn_id=turn_id,
            speaker=role,
            text=final_text.strip(),
            duration_ms=duration_ms,
        )

        await self._emit_event(final_event)

        # Trigger downstream orchestrator for customer turns
        if role == EventRole.CUSTOMER and self.orchestrator is not None:
            try:
                await self.orchestrator.handle_customer_turn(
                    session_id=session_id,
                    turn_id=turn_id,
                    utterance_text=final_text.strip(),
                )
            except Exception as e:
                logger.error("Orchestrator customer turn dispatch failed: %s", e)

        return final_event

    async def handle_manual_transcript(self, event: TranscriptManualEvent) -> TranscriptFinalEvent:
        """Handle agent or customer manually submitted text turn."""
        turn_id = self._next_turn_id(event.session_id)
        final_event = TranscriptFinalEvent(
            session_id=event.session_id,
            turn_id=turn_id,
            speaker=event.speaker,
            text=event.text.strip(),
            duration_ms=0.0,
        )

        await self._emit_event(final_event)

        if event.speaker == EventRole.CUSTOMER and self.orchestrator is not None:
            try:
                await self.orchestrator.handle_customer_turn(
                    session_id=event.session_id,
                    turn_id=turn_id,
                    utterance_text=event.text.strip(),
                )
            except Exception as e:
                logger.error("Orchestrator manual customer turn dispatch failed: %s", e)

        return final_event
