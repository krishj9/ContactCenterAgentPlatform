"""Summary Service v2 (P5.11, Spec §3.4).

Generates structured end-of-call summaries and CRM case notes linking transcript turns
to completed actions, issue updates, and agent disposition.
"""

from __future__ import annotations

import logging
from typing import Any

from app.contracts.events_v1 import SummaryReadyEvent
from app.core.container import Container
from app.domain.summary import CallSummary

logger = logging.getLogger(__name__)


class SummaryService:
    """Orchestrates structured post-call summarization and CRM case note drafting."""

    def __init__(self, container: Container | None = None) -> None:
        self.container = container or Container()

    async def generate_call_summary(
        self,
        session_id: str,
        transcript_turns: list[dict[str, Any]],
        accepted_actions: list[str] | None = None,
        disposition: str | None = None,
    ) -> tuple[CallSummary, SummaryReadyEvent]:
        """Generate structured summary from session dialogue and completed actions."""
        # 1. Generate via Container's Generator port (with deterministic fallback)
        summary: CallSummary = await self.container.generator.generate_summary(
            session_id=session_id,
            transcript_turns=transcript_turns,
        )

        # 2. Enrich with accepted action items and disposition if provided
        actions_completed = list(summary.actions_completed)
        if accepted_actions:
            actions_completed = list(dict.fromkeys(actions_completed + accepted_actions))

        case_notes = summary.crm_case_note
        if disposition:
            case_notes = f"{case_notes}\n- Agent Disposition: {disposition.upper()}"

        enriched_summary = CallSummary(
            summary_id=summary.summary_id,
            session_id=summary.session_id,
            call_overview=summary.call_overview,
            key_issues=summary.key_issues,
            actions_completed=actions_completed,
            required_followups=summary.required_followups,
            crm_case_note=case_notes,
            created_at=summary.created_at,
        )

        # 3. Create SummaryReadyEvent outbound WebSocket event
        event = SummaryReadyEvent(
            session_id=session_id,
            call_overview=enriched_summary.call_overview,
            key_issues=enriched_summary.key_issues,
            actions_completed=enriched_summary.actions_completed,
            required_followups=enriched_summary.required_followups,
            crm_case_note=enriched_summary.crm_case_note,
        )

        return enriched_summary, event
