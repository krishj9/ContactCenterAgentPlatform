"""Deterministic Grounding & Guardrail State Machine (P5.8, Spec §3.3.3).

Evaluates calibrated thresholds, policy presence, and NLI verification in strict order:
1. Low intent confidence / OOS -> LOW_CONFIDENCE
2. Missing evidence chunks < tau_evidence -> MISSING_EVIDENCE
3. Missing policy procedure < tau_policy -> POLICY_REVIEW_NEEDED
4. Contradiction detected -> LOW_CONFIDENCE (forced)
5. Verifier dropped > 30% claims -> LOW_CONFIDENCE
6. LLM abstains -> MISSING_EVIDENCE
7. Otherwise -> GROUNDED
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from app.domain.evidence import EvidenceChunk
from app.domain.grounding import GroundingDecision, GroundingState
from app.domain.intent import IntentPrediction
from app.services.rag.verifier import VerificationResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GroundingEvaluation:
    """Outcome of Grounding State Machine evaluation."""

    state: GroundingState
    warning_code: str | None = None
    warning_message: str | None = None
    is_suppressed: bool = False
    policy_supported: bool = False
    matched_chunk_ids: list[str] = field(default_factory=list)

    @property
    def is_grounded(self) -> bool:
        return self.state == GroundingState.GROUNDED and self.policy_supported

    def to_decision(self) -> GroundingDecision:
        return GroundingDecision(
            state=self.state,
            policy_supported=self.policy_supported,
            matched_chunk_ids=self.matched_chunk_ids,
            rejection_reason=self.warning_message,
        )


class DeterministicGroundingStateMachine:
    """Evaluates grounding state based on calibrated scores and verified citations."""

    def __init__(
        self,
        config_path: Path | str | None = None,
        tau_intent: float = 0.55,
        tau_evidence: float = 0.48,
        tau_policy: float = 0.68,
        verifier_drop_tolerance: float = 0.30,
    ) -> None:
        if config_path:
            self.config_path = Path(config_path)
        else:
            candidates = [
                Path("config/grounding.yaml"),
                Path(__file__).resolve().parents[4] / "config" / "grounding.yaml",
                Path(__file__).resolve().parents[3] / "config" / "grounding.yaml",
            ]
            self.config_path = next((c for c in candidates if c.exists()), candidates[1])

        self.tau_intent = tau_intent
        self.tau_evidence = tau_evidence
        self.tau_policy = tau_policy
        self.verifier_drop_tolerance = verifier_drop_tolerance

        self._load_config()

    def _load_config(self) -> None:
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                t = data.get("thresholds", {})
                self.tau_intent = float(t.get("tau_intent", self.tau_intent))
                self.tau_evidence = float(t.get("tau_evidence", self.tau_evidence))
                self.tau_policy = float(t.get("tau_policy", self.tau_policy))
                self.verifier_drop_tolerance = float(
                    t.get("verifier_drop_tolerance", self.verifier_drop_tolerance)
                )
            except Exception as e:
                logger.error(f"Failed to load grounding thresholds from {self.config_path}: {e}")

    def evaluate(
        self,
        intent: IntentPrediction,
        evidence: list[EvidenceChunk],
        requires_policy: bool = True,
        verification: VerificationResult | None = None,
        llm_abstains: bool = False,
    ) -> GroundingEvaluation:
        """Evaluate grounding conditions in strict priority order (Spec §3.3.3)."""
        # Condition 1: Intent is OOS or p1 < tau_intent (Spec §3.3.3 line 360)
        if intent.is_out_of_scope or intent.confidence < self.tau_intent:
            return GroundingEvaluation(
                state=GroundingState.LOW_CONFIDENCE,
                warning_code="LOW_INTENT_CONFIDENCE",
                warning_message=f"Intent confidence ({intent.confidence:.2f}) is below threshold {self.tau_intent:.2f} or out of scope.",
                is_suppressed=True,
                policy_supported=False,
            )

        # Condition 2: No FAQ or policy chunk >= tau_evidence (Spec §3.3.3 line 361)
        evidence_chunks = [c for c in evidence if c.similarity_score >= self.tau_evidence]
        if not evidence_chunks:
            return GroundingEvaluation(
                state=GroundingState.MISSING_EVIDENCE,
                warning_code="MISSING_EVIDENCE",
                warning_message=f"No retrieved policy or FAQ chunks met the minimum evidence threshold ({self.tau_evidence:.2f}).",
                is_suppressed=True,
                policy_supported=False,
            )

        # Condition 3: Intent requires policy and no policy chunk >= tau_policy (Spec §3.3.3 line 362)
        policy_chunks = [
            c for c in evidence if c.is_policy and c.similarity_score >= self.tau_policy
        ]
        if requires_policy and not policy_chunks:
            return GroundingEvaluation(
                state=GroundingState.POLICY_REVIEW_NEEDED,
                warning_code="MISSING_POLICY_SUPPORT",
                warning_message=f"Intent requires authoritative policy procedure, but no chunk scored >= tau_policy ({self.tau_policy:.2f}).",
                is_suppressed=False,
                policy_supported=False,
                matched_chunk_ids=[c.chunk_id for c in evidence_chunks],
            )

        # Condition 4: NLI detects contradiction (Spec §3.3.3 line 363)
        if verification and verification.contradiction_detected:
            return GroundingEvaluation(
                state=GroundingState.LOW_CONFIDENCE,
                warning_code="CONFLICTING_EVIDENCE",
                warning_message="NLI contradiction detected between claims and authoritative policy guidance.",
                is_suppressed=False,
                policy_supported=False,
                matched_chunk_ids=verification.valid_citation_ids,
            )

        # Condition 5: Verifier drops > 30% claims as uncited / unentailed (Spec §3.3.3 line 364)
        if verification and verification.dropped_ratio > self.verifier_drop_tolerance:
            return GroundingEvaluation(
                state=GroundingState.LOW_CONFIDENCE,
                warning_code="LOW_CONFIDENCE_UNVERIFIED_CLAIMS",
                warning_message=f"Verifier dropped {verification.dropped_ratio:.1%} of claims (> {self.verifier_drop_tolerance:.1%} tolerance).",
                is_suppressed=False,
                policy_supported=len(policy_chunks) > 0,
                matched_chunk_ids=verification.valid_citation_ids,
            )

        # Condition 6: LLM abstains (Spec §3.3.3 line 365)
        if llm_abstains:
            return GroundingEvaluation(
                state=GroundingState.MISSING_EVIDENCE,
                warning_code="LLM_ABSTAINED",
                warning_message="Generation model explicitly abstained due to insufficient ground-truth evidence.",
                is_suppressed=True,
                policy_supported=False,
            )

        # Condition 7: GROUNDED (Spec §3.3.3 line 366)
        matched_ids = [c.chunk_id for c in (policy_chunks if requires_policy else evidence_chunks)]
        if verification and verification.valid_citation_ids:
            matched_ids = list(dict.fromkeys(matched_ids + verification.valid_citation_ids))

        return GroundingEvaluation(
            state=GroundingState.GROUNDED,
            warning_code=None,
            warning_message=None,
            is_suppressed=False,
            policy_supported=True,
            matched_chunk_ids=matched_ids,
        )
