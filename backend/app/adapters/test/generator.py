"""Test adapter for Generator port."""

from __future__ import annotations

from typing import Any

from app.domain.evidence import EvidenceChunk
from app.domain.grounding import GroundingDecision, GroundingState
from app.domain.intent import IntentPrediction
from app.domain.recommendation import (
    ActionType,
    NextBestAction,
    SuggestedResponse,
)
from app.domain.summary import CallSummary


class TestGenerator:
    """Deterministic structured generator producing grounded actions and summaries."""

    __test__ = False

    async def generate_action(
        self,
        intent: IntentPrediction,
        evidence: list[EvidenceChunk],
        customer_context: dict[str, Any] | None = None,
    ) -> tuple[NextBestAction, SuggestedResponse]:
        policy_chunks = [c for c in evidence if c.is_policy]
        has_policy = len(policy_chunks) > 0
        citation_ids = [c.chunk_id for c in evidence[:2]]

        grounding = GroundingDecision(
            state=GroundingState.GROUNDED if has_policy else GroundingState.POLICY_REVIEW_NEEDED,
            policy_supported=has_policy,
            matched_chunk_ids=citation_ids,
            entailment_score=0.96 if has_policy else 0.40,
            rejection_reason=None if has_policy else "No active policy evidence available",
        )

        action = NextBestAction(
            action_id=f"act-{intent.intent_label}-01",
            title=f"Resolve {intent.intent_label.replace('_', ' ').title()}",
            description=f"Actionable guidance for {intent.intent_label}.",
            action_type=ActionType.PROCEDURAL if has_policy else ActionType.GUIDANCE,
            steps=[
                "Verify customer identity and recent account ledger.",
                "Review applicable bank policy terms with customer.",
                "Execute remediation in core banking portal.",
            ],
            grounding=grounding,
            citations=citation_ids,
            confidence=0.94,
        )

        response = SuggestedResponse(
            response_id=f"resp-{intent.intent_label}-01",
            text=f"I can certainly help you with your {intent.intent_label.replace('_', ' ')}. Let me pull up your account records.",
            rationale=f"Addresses detected customer intent ({intent.intent_label}).",
            grounding=grounding,
            citations=citation_ids,
            is_editable=True,
        )

        return action, response

    async def generate_summary(
        self,
        session_id: str,
        transcript_turns: list[dict[str, Any]],
    ) -> CallSummary:
        text_joined = " ".join(t.get("text", "") for t in transcript_turns)
        return CallSummary(
            summary_id=f"sum-{session_id}",
            session_id=session_id,
            call_overview=f"Customer call with {len(transcript_turns)} turns discussing banking operations.",
            key_issues=["Inquiry addressed during session: " + text_joined[:80] + "..."],
            actions_completed=["Verified caller authentication", "Provided policy guidance"],
            required_followups=["Customer follow-up as necessary"],
            crm_case_note="CASE-" + session_id[:8] + ": Call concluded successfully.",
        )
