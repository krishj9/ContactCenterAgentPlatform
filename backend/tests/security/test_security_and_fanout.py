"""Tests for Phase P6: Signed join tokens, single-use jti, and role-based outbound event isolation."""

from __future__ import annotations

from typing import Any

import pytest

from app.contracts.events_v1 import (
    AssistRecommendationEvent,
    EventRole,
    GuardrailAlertEvent,
    GuardrailSeverity,
    IssueUpdateEvent,
    NextBestActionPayload,
    SuggestedResponsePayload,
    SummaryReadyEvent,
    TranscriptFinalEvent,
    TranscriptPartialEvent,
)
from app.core.security import (
    InvalidSignatureError,
    SecurityManager,
    TokenExpiredError,
    TokenReplayError,
    TokenValidationError,
)
from app.domain.grounding import GroundingState
from app.ws.fanout import OutboundEventFilter
from app.ws.session import SessionConnectionManager


class MockWebSocket:
    """Mock WebSocket storing transmitted text payloads."""

    def __init__(self) -> None:
        self.sent_messages: list[str] = []
        self.closed = False

    async def send_text(self, text: str) -> None:
        self.sent_messages.append(text)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_jwt_token_generation_and_verification() -> None:
    sec = SecurityManager(secret_key="test-secret-key-12345678901234567890")
    session_id = "sess_card_declined_101"
    participant_id = "agent_4029"
    role = "agent"

    token = sec.create_join_token(
        session_id=session_id,
        participant_id=participant_id,
        role=role,
        ttl_seconds=900,
    )

    assert isinstance(token, str)
    assert len(token.split(".")) == 3

    # Verification passes
    payload = await sec.verify_join_token(
        token=token,
        expected_session_id=session_id,
        check_single_use=False,
    )
    assert payload.sub == participant_id
    assert payload.session_id == session_id
    assert payload.role == role
    assert payload.exp > payload.iat


@pytest.mark.asyncio
async def test_jwt_token_invalid_signature_rejected() -> None:
    sec1 = SecurityManager(secret_key="secret-key-one-01234567890123456789")
    sec2 = SecurityManager(secret_key="secret-key-two-01234567890123456789")

    token = sec1.create_join_token(
        session_id="sess_abc",
        participant_id="user_1",
        role="customer",
    )

    with pytest.raises(InvalidSignatureError):
        await sec2.verify_join_token(token, expected_session_id="sess_abc")


@pytest.mark.asyncio
async def test_jwt_token_expired_rejected() -> None:
    sec = SecurityManager(secret_key="test-secret-key")

    # Negative TTL creates already expired token
    token = sec.create_join_token(
        session_id="sess_expired",
        participant_id="user_2",
        role="customer",
        ttl_seconds=-10,
    )

    with pytest.raises(TokenExpiredError):
        await sec.verify_join_token(token, expected_session_id="sess_expired")


@pytest.mark.asyncio
async def test_jwt_token_session_mismatch_rejected() -> None:
    sec = SecurityManager(secret_key="test-secret-key")
    token = sec.create_join_token(
        session_id="sess_correct",
        participant_id="user_3",
        role="customer",
    )

    with pytest.raises(TokenValidationError, match="does not match expected"):
        await sec.verify_join_token(token, expected_session_id="sess_wrong")


@pytest.mark.asyncio
async def test_single_use_jti_blocks_replay() -> None:
    sec = SecurityManager(secret_key="test-secret-key")
    token = sec.create_join_token(
        session_id="sess_replay",
        participant_id="user_4",
        role="customer",
    )

    # First verification succeeds and consumes jti
    payload = await sec.verify_join_token(
        token, expected_session_id="sess_replay", check_single_use=True
    )
    assert payload.session_id == "sess_replay"

    # Second verification with same token fails with TokenReplayError
    with pytest.raises(TokenReplayError, match="has already been consumed"):
        await sec.verify_join_token(token, expected_session_id="sess_replay", check_single_use=True)


def test_outbound_event_filter_customer_isolation() -> None:
    """Critical safety invariant R9, R14: Customer sockets must NEVER receive internal assist events."""
    # 1. AssistRecommendationEvent must be blocked for customer
    recommendation_event = AssistRecommendationEvent(
        session_id="sess_101",
        turn_id=2,
        recommendations=[
            NextBestActionPayload(
                action_id="act_1",
                title="Override Rule",
                description="Lift terminal rule",
                action_type="PROCEDURAL",
                steps=["Step 1"],
                is_grounded=True,
                grounding_state=GroundingState.GROUNDED,
                citations=["pol_1"],
            )
        ],
        suggested_response=SuggestedResponsePayload(
            response_id="resp_1",
            text="I will lift the rule.",
            rationale="Internal guideline",
            is_editable=True,
            grounding_state=GroundingState.GROUNDED,
            citations=["pol_1"],
        ),
        grounding_state=GroundingState.GROUNDED,
    )

    customer_result = OutboundEventFilter.filter_event_for_role(recommendation_event, "customer")
    assert customer_result is None, "Assist recommendations must be suppressed for customer role"

    agent_result = OutboundEventFilter.filter_event_for_role(recommendation_event, "agent")
    assert agent_result is not None, "Assist recommendations must be delivered to agent role"
    assert agent_result["type"] == "assist.recommendation"

    # 2. IssueUpdateEvent must be blocked for customer
    issue_event = IssueUpdateEvent(
        session_id="sess_101",
        turn_id=2,
        intent_label="card_declined",
        confidence=0.95,
        is_out_of_scope=False,
    )
    assert OutboundEventFilter.filter_event_for_role(issue_event, "customer") is None
    assert OutboundEventFilter.filter_event_for_role(issue_event, "agent") is not None

    # 3. GuardrailAlertEvent must be blocked for customer
    alert_event = GuardrailAlertEvent(
        session_id="sess_101",
        code="POLICY_REVIEW_NEEDED",
        message="Internal compliance hold",
        severity=GuardrailSeverity.WARNING,
    )
    assert OutboundEventFilter.filter_event_for_role(alert_event, "customer") is None
    assert OutboundEventFilter.filter_event_for_role(alert_event, "agent") is not None

    # 4. SummaryReadyEvent must be blocked for customer
    summary_event = SummaryReadyEvent(
        session_id="sess_101",
        call_overview="Overview",
        key_issues=["Issue"],
        actions_completed=["Action"],
        required_followups=[],
        crm_case_note="Internal CRM note",
    )
    assert OutboundEventFilter.filter_event_for_role(summary_event, "customer") is None
    assert OutboundEventFilter.filter_event_for_role(summary_event, "agent") is not None

    # 5. Customer dialogue events must be allowed for both customer and agent
    partial_event = TranscriptPartialEvent(
        session_id="sess_101",
        turn_id=2,
        speaker=EventRole.CUSTOMER,
        text="My card was declined",
    )
    assert OutboundEventFilter.filter_event_for_role(partial_event, "customer") is not None
    assert OutboundEventFilter.filter_event_for_role(partial_event, "agent") is not None

    final_event = TranscriptFinalEvent(
        session_id="sess_101",
        turn_id=2,
        speaker=EventRole.CUSTOMER,
        text="My card was declined in Paris",
    )
    assert OutboundEventFilter.filter_event_for_role(final_event, "customer") is not None
    assert OutboundEventFilter.filter_event_for_role(final_event, "agent") is not None


@pytest.mark.asyncio
async def test_session_connection_manager_broadcast_enforces_isolation() -> None:
    """Verify SessionConnectionManager transmits assist events to agent but 0 events to customer."""
    manager = SessionConnectionManager()
    session_id = "sess_security_test"

    agent_ws = MockWebSocket()
    customer_ws = MockWebSocket()

    manager.register(session_id, "agent_1", "agent", agent_ws)  # type: ignore[arg-type]
    manager.register(session_id, "cust_1", "customer", customer_ws)  # type: ignore[arg-type]

    # Broadcast dialogue event (allowed for both)
    dialogue_evt = TranscriptFinalEvent(
        session_id=session_id,
        turn_id=1,
        speaker=EventRole.CUSTOMER,
        text="Hello, I need help.",
    )
    await manager.broadcast(session_id, dialogue_evt)

    assert len(agent_ws.sent_messages) == 1
    assert len(customer_ws.sent_messages) == 1

    # Broadcast internal recommendation event (prohibited for customer)
    nba_evt = AssistRecommendationEvent(
        session_id=session_id,
        turn_id=1,
        recommendations=[
            NextBestActionPayload(
                action_id="act_override",
                title="Geographic Override",
                description="Lift terminal rule",
                action_type="PROCEDURAL",
                steps=["Step 1"],
                is_grounded=True,
                grounding_state=GroundingState.GROUNDED,
            )
        ],
        grounding_state=GroundingState.GROUNDED,
    )
    await manager.broadcast(session_id, nba_evt)

    # Agent received the recommendation
    assert len(agent_ws.sent_messages) == 2
    assert "assist.recommendation" in agent_ws.sent_messages[1]

    # Customer received ZERO assist events (count remains 1)
    assert len(customer_ws.sent_messages) == 1, (
        "Customer socket received internal assist event! Invariant violation."
    )


@pytest.mark.asyncio
async def test_transcription_service_handles_audio_and_finalizes_turn() -> None:
    from app.adapters.local.whisper_stt import LocalFasterWhisperSTT
    from app.contracts.events_v1 import AudioChunkEvent
    from app.services.transcription import TranscriptionService

    stt = LocalFasterWhisperSTT()
    emitted_events: list[str] = []

    async def _callback(evt: Any) -> None:
        emitted_events.append(evt.type)

    svc = TranscriptionService(stt_adapter=stt, event_callback=_callback)

    # Send 100ms audio chunk (1600 samples of 16-bit PCM silence)
    silent_pcm = b"\x00\x00" * 1600
    chunk_evt = AudioChunkEvent(
        session_id="sess_audio",
        participant_id="cust_88",
        role=EventRole.CUSTOMER,
        seq=0,
    )
    await svc.handle_audio_chunk(chunk_evt, silent_pcm)

    # Finalize utterance
    final_evt = await svc.finalize_utterance(
        session_id="sess_audio",
        participant_id="cust_88",
        role=EventRole.CUSTOMER,
        final_text="My card was declined at Paris restaurant.",
    )

    assert final_evt.type == "transcript.final"
    assert final_evt.text == "My card was declined at Paris restaurant."
    assert "transcript.final" in emitted_events
