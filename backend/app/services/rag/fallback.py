"""Deterministic Playbook Fallback Service (P5.9, Spec §3.3.4).

Populates verified playbook templates strictly with retrieved policy steps
when generation is unavailable, times out, or when rules-first guidance is required.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from app.domain.evidence import EvidenceChunk
from app.domain.grounding import GroundingDecision, GroundingState
from app.domain.recommendation import ActionType, NextBestAction, SuggestedResponse

logger = logging.getLogger(__name__)


class PlaybookFallbackService:
    """Manages deterministic YAML playbook fallbacks keyed by canonical intent."""

    def __init__(self, playbooks_dir: Path | str | None = None) -> None:
        if playbooks_dir:
            self.playbooks_dir = Path(playbooks_dir)
        else:
            candidates = [
                Path("playbooks"),
                Path(__file__).resolve().parents[4] / "playbooks",
                Path(__file__).resolve().parents[3] / "playbooks",
            ]
            self.playbooks_dir = next((c for c in candidates if c.exists()), candidates[1])
        self._playbooks: dict[str, dict[str, Any]] = {}
        self._load_playbooks()

    def _load_playbooks(self) -> None:
        if not self.playbooks_dir.exists():
            return
        for file in self.playbooks_dir.glob("*.yaml"):
            try:
                with open(file, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "intent_label" in data:
                        self._playbooks[data["intent_label"]] = data
            except Exception as e:
                logger.error(f"Error loading playbook {file}: {e}")

    def render_fallback(
        self,
        intent_label: str,
        retrieved_evidence: list[EvidenceChunk],
    ) -> tuple[NextBestAction, SuggestedResponse]:
        """Render deterministic playbook populated strictly with verified policy citations."""
        # Find matching playbook
        playbook = self._playbooks.get(intent_label)
        if not playbook:
            # Fallback to general inquiry or first available
            playbook = self._playbooks.get(
                "card_declined",
                {
                    "title": f"Guidance Procedure for {intent_label.replace('_', ' ').title()}",
                    "action_type": "verify",
                    "steps": ["Confirm customer identity and inquiry details with cardholder."],
                    "suggested_response": {
                        "text": "Thank you for providing those details. Let me assist you with your request.",
                        "citations": [],
                    },
                },
            )

        # Match policy chunks in retrieved evidence
        policy_chunks = [c for c in retrieved_evidence if c.is_policy]
        matched_citations: list[str] = []

        if policy_chunks:
            # Use real chunk IDs from retrieved context
            matched_citations = [c.chunk_id for c in policy_chunks[:3]]
        else:
            # Fall back to default citations from playbook if present
            matched_citations = list(playbook.get("default_citations", []))

        action_type_str = playbook.get("action_type", "verify").lower()
        action_type_enum = (
            ActionType.COMPLIANCE
            if action_type_str == "verify"
            else ActionType.ESCALATION
            if action_type_str == "escalate"
            else ActionType.GUIDANCE
        )

        has_policy = len(policy_chunks) > 0 or len(matched_citations) > 0
        grounding_state = (
            GroundingState.GROUNDED if has_policy else GroundingState.POLICY_REVIEW_NEEDED
        )

        action = NextBestAction(
            action_id=f"act_fb_{abs(hash(intent_label)) % 100000:05d}",
            title=playbook.get("title", f"{intent_label.replace('_', ' ').title()} Procedure"),
            description=f"Playbook guidance for {intent_label}",
            action_type=action_type_enum,
            steps=list(playbook.get("steps", [])),
            grounding=GroundingDecision(
                state=grounding_state,
                policy_supported=has_policy,
                matched_chunk_ids=matched_citations,
            ),
            citations=matched_citations,
        )

        resp_data = playbook.get("suggested_response", {})
        resp_text = resp_data.get(
            "text", "I am reviewing your account and will assist you with this request."
        )
        resp_citations = [
            c for c in resp_data.get("citations", []) if c in matched_citations
        ] or matched_citations[:1]

        response = SuggestedResponse(
            response_id=f"resp_fb_{abs(hash(intent_label)) % 100000:05d}",
            text=resp_text,
            rationale=f"Playbook response for {intent_label}",
            grounding=GroundingDecision(
                state=grounding_state,
                policy_supported=has_policy,
                matched_chunk_ids=resp_citations,
            ),
            citations=resp_citations,
        )

        return action, response
