"""Unit tests for RealtimeOrchestrator and customer turn debounce (P4.10)."""

import pytest

from app.contracts.events_v1 import (
    EventRole,
    GuardrailAlertEvent,
    IssueUpdateEvent,
    TranscriptFinalEvent,
)
from app.core.container import Container
from app.services.realtime_orchestrator import RealtimeOrchestrator


@pytest.mark.asyncio
async def test_orchestrator_customer_turn_emits_issue_update():
    """Verify that customer turn emits transcript.final and issue.update event."""
    container = Container()
    orchestrator = RealtimeOrchestrator(container=container, debounce_ms=10)

    events = await orchestrator.handle_transcript_final(
        session_id="sess_test_101",
        turn_id=1,
        speaker=EventRole.CUSTOMER,
        text="My debit card was just declined at the grocery store.",
    )

    assert len(events) >= 2
    assert any(isinstance(e, TranscriptFinalEvent) for e in events)

    issue_events = [e for e in events if isinstance(e, IssueUpdateEvent)]
    assert len(issue_events) == 1
    issue = issue_events[0]
    assert issue.intent_label == "card_declined"
    assert issue.confidence > 0.70
    assert issue.is_out_of_scope is False
    assert len(issue.candidates) > 0


@pytest.mark.asyncio
async def test_orchestrator_agent_turn_does_not_trigger_intent():
    """Verify that agent turns emit transcript.final but do not trigger issue.update."""
    container = Container()
    orchestrator = RealtimeOrchestrator(container=container, debounce_ms=10)

    events = await orchestrator.handle_transcript_final(
        session_id="sess_test_102",
        turn_id=1,
        speaker=EventRole.AGENT,
        text="Hello, thank you for calling Premier Card support.",
    )

    assert len(events) == 1
    assert isinstance(events[0], TranscriptFinalEvent)
    assert not any(isinstance(e, IssueUpdateEvent) for e in events)


@pytest.mark.asyncio
async def test_orchestrator_out_of_scope_triggers_guardrail_alert():
    """Verify that out-of-scope customer speech triggers GuardrailAlertEvent."""
    container = Container()
    orchestrator = RealtimeOrchestrator(container=container, debounce_ms=10)

    events = await orchestrator.handle_transcript_final(
        session_id="sess_test_103",
        turn_id=1,
        speaker=EventRole.CUSTOMER,
        text="What is the weather like outside today?",
    )

    alerts = [e for e in events if isinstance(e, GuardrailAlertEvent)]
    assert len(alerts) == 1
    assert alerts[0].code == "OUT_OF_SCOPE"
