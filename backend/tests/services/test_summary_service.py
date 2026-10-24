"""Unit tests for SummaryService v2 (P5.11)."""

from __future__ import annotations

import pytest

from app.contracts.events_v1 import SummaryReadyEvent
from app.core.container import Container
from app.services.summary_service import SummaryService


@pytest.mark.asyncio
async def test_summary_service_generates_case_notes_and_event():
    """Verify that SummaryService generates CallSummary and SummaryReadyEvent."""
    container = Container()
    service = SummaryService(container=container)

    turns = [
        {"turn_id": 1, "speaker": "agent", "text": "Hello, thank you for calling Premier support."},
        {"turn_id": 2, "speaker": "customer", "text": "My card was declined at checkout in Paris."},
        {"turn_id": 3, "speaker": "agent", "text": "I can lift this 24h geographic security hold."},
    ]

    summary, event = await service.generate_call_summary(
        session_id="sess_sum_101",
        transcript_turns=turns,
        accepted_actions=["Lift 24-hour security block on terminal."],
        disposition="resolved",
    )

    assert summary.session_id == "sess_sum_101"
    assert len(summary.call_overview) > 10
    assert "Lift 24-hour security block on terminal." in summary.actions_completed
    assert "RESOLVED" in summary.crm_case_note

    assert isinstance(event, SummaryReadyEvent)
    assert event.session_id == "sess_sum_101"
    assert len(event.actions_completed) > 0
