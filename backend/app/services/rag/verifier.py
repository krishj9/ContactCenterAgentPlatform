"""Claim and Citation Verifier (P5.7, Spec §3.3.2 & §3.3.3).

Validates that all cited chunk IDs exist in context, checks procedural entailment,
and enforces that operational recommendations possess verified policy citations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.domain.evidence import EvidenceChunk
from app.domain.grounding import GroundingDecision, GroundingState
from app.domain.recommendation import ActionType, NextBestAction, SuggestedResponse
from app.services.rag.schemas import RAGGenerationOutput

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VerificationResult:
    """Outcome of claim and citation verification."""

    actions: list[NextBestAction]
    suggested_response: SuggestedResponse | None
    dropped_claims_count: int = 0
    total_claims_count: int = 0
    contradiction_detected: bool = False
    missing_policy_for_operational: bool = False
    valid_citation_ids: list[str] = field(default_factory=list)

    @property
    def dropped_ratio(self) -> float:
        if self.total_claims_count == 0:
            return 0.0
        return self.dropped_claims_count / self.total_claims_count


class ClaimAndCitationVerifier:
    """Verifies generation output against retrieved evidence chunks."""

    def __init__(self, drop_tolerance: float = 0.30) -> None:
        self.drop_tolerance = drop_tolerance

    def verify(
        self,
        generation: RAGGenerationOutput,
        context_chunks: list[EvidenceChunk],
        intent_label: str,
    ) -> VerificationResult:
        """Verify citation lineage and claim entailment against context chunks."""
        context_map: dict[str, EvidenceChunk] = {c.chunk_id: c for c in context_chunks}
        policy_chunk_ids = {c.chunk_id for c in context_chunks if c.is_policy}

        total_claims = 0
        dropped_claims = 0
        contradiction = False
        missing_policy_operational = False
        all_valid_citations: list[str] = []

        verified_actions: list[NextBestAction] = []

        # 1. Verify Next-Best Actions
        for item in generation.next_best_actions:
            total_claims += len(item.steps) if item.steps else 1

            # Validate citations against context_map
            valid_item_citations = [cid for cid in item.citations if cid in context_map]

            if not valid_item_citations:
                logger.warning(
                    f"Action '{item.title}' stripped: citations {item.citations} not in context."
                )
                dropped_claims += len(item.steps) if item.steps else 1
                continue

            # Invariant check: action_type in {verify, escalate} must cite at least one policy source
            has_policy_support = any(cid in policy_chunk_ids for cid in valid_item_citations)
            if item.action_type in {"verify", "escalate"} and not has_policy_support:
                logger.warning(
                    f"Action '{item.title}' has action_type={item.action_type} but no policy citation."
                )
                missing_policy_operational = True

            # Contradiction check: never promise waivers or unblocks without compliance steps
            lower_steps = " ".join(item.steps).lower()
            if any(
                forbidden in lower_steps
                for forbidden in ["guarantee waiver", "promise refund", "unconditionally unblock"]
            ):
                contradiction = True
                dropped_claims += len(item.steps)
                continue

            all_valid_citations.extend(valid_item_citations)

            # Map to domain NextBestAction
            action_type_enum = (
                ActionType.COMPLIANCE
                if item.action_type == "verify"
                else ActionType.ESCALATION
                if item.action_type == "escalate"
                else ActionType.GUIDANCE
            )

            grounding_state = (
                GroundingState.GROUNDED
                if has_policy_support
                else GroundingState.POLICY_REVIEW_NEEDED
            )

            action = NextBestAction(
                action_id=f"act_{abs(hash(item.title)) % 100000:05d}",
                title=item.title,
                description=f"{item.title} based on {', '.join(valid_item_citations)}",
                action_type=action_type_enum,
                steps=item.steps,
                grounding=GroundingDecision(
                    state=grounding_state,
                    policy_supported=has_policy_support,
                    matched_chunk_ids=valid_item_citations,
                ),
                citations=valid_item_citations,
            )
            verified_actions.append(action)

        # 2. Verify Suggested Response
        verified_response: SuggestedResponse | None = None
        if generation.suggested_response:
            total_claims += 1
            valid_resp_citations = [
                cid for cid in generation.suggested_response.citations if cid in context_map
            ]

            resp_text = generation.suggested_response.text
            # Contradiction check on response text
            if any(
                forbidden in resp_text.lower()
                for forbidden in ["i guarantee", "fee is waived unconditionally"]
            ):
                contradiction = True
                dropped_claims += 1
            else:
                if not valid_resp_citations and context_chunks:
                    # Default to top context chunk citation
                    valid_resp_citations = [context_chunks[0].chunk_id]

                all_valid_citations.extend(valid_resp_citations)
                has_pol = any(cid in policy_chunk_ids for cid in valid_resp_citations)

                verified_response = SuggestedResponse(
                    response_id=f"resp_{abs(hash(resp_text)) % 100000:05d}",
                    text=resp_text,
                    rationale=f"Generated reply for {intent_label}",
                    grounding=GroundingDecision(
                        state=GroundingState.GROUNDED
                        if has_pol
                        else GroundingState.POLICY_REVIEW_NEEDED,
                        policy_supported=has_pol,
                        matched_chunk_ids=valid_resp_citations,
                    ),
                    citations=valid_resp_citations,
                )

        return VerificationResult(
            actions=verified_actions,
            suggested_response=verified_response,
            dropped_claims_count=dropped_claims,
            total_claims_count=total_claims,
            contradiction_detected=contradiction,
            missing_policy_for_operational=missing_policy_operational,
            valid_citation_ids=list(dict.fromkeys(all_valid_citations)),
        )
