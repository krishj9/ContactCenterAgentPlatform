"""Intent Decision Layer & Multi-Issue Ambiguity Rule (Spec §3.2.1, P4.4).

Applies calibrated temperature scaling, multi-issue ambiguity rule, and out-of-scope (OOS) thresholding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ml.intent.calibrate import softmax


@dataclass(frozen=True)
class IntentScoredCandidate:
    """Scored intent candidate with calibrated confidence."""

    intent_label: str
    confidence: float


@dataclass(frozen=True)
class ClassificationDecision:
    """Final decision output from the intent classification layer."""

    intent_label: str
    confidence: float
    is_out_of_scope: bool
    candidates: list[IntentScoredCandidate]
    is_ambiguous_multi_issue: bool
    explanation_exemplar_ids: list[str] = field(default_factory=list)


class IntentDecisionLayer:
    """Evaluates raw model logits through calibrated thresholds and governance rules."""

    def __init__(
        self,
        id2label: dict[int, str] | list[str],
        temperature: float = 1.0,
        tau_oos: float = 0.55,
        multi_issue_p2_min: float = 0.25,
        multi_issue_delta_max: float = 0.30,
    ) -> None:
        if isinstance(id2label, list):
            self.id2label = {i: lbl for i, lbl in enumerate(id2label)}
        else:
            self.id2label = {int(k): v for k, v in id2label.items()}

        self.temperature = max(1e-4, float(temperature))
        self.tau_oos = float(tau_oos)
        self.multi_issue_p2_min = float(multi_issue_p2_min)
        self.multi_issue_delta_max = float(multi_issue_delta_max)

    def decide_from_probabilities(
        self,
        probabilities: list[float],
        top_k: int = 3,
        exemplar_ids: list[str] | None = None,
    ) -> ClassificationDecision:
        """Apply decision rules to calibrated probability distribution."""
        ranked_indices = sorted(
            range(len(probabilities)),
            key=lambda i: probabilities[i],
            reverse=True,
        )

        top_indices = ranked_indices[: max(1, top_k)]
        candidates = [
            IntentScoredCandidate(
                intent_label=self.id2label.get(idx, f"label_{idx}"),
                confidence=round(probabilities[idx], 4),
            )
            for idx in top_indices
        ]

        top_candidate = candidates[0]
        top_label = top_candidate.intent_label
        p1 = top_candidate.confidence

        # Spec §3.2.1 Multi-issue ambiguity rule:
        # Return top-2 labels when p2 >= 0.25 and p1 - p2 < 0.30
        is_ambiguous = False
        if len(candidates) >= 2:
            p2 = candidates[1].confidence
            if p2 >= self.multi_issue_p2_min and (p1 - p2) < self.multi_issue_delta_max:
                is_ambiguous = True

        # Out-of-scope determination:
        # (a) explicit out_of_scope class, or (b) max-softmax threshold tau_oos
        is_oos = False
        if top_label == "out_of_scope" or p1 < self.tau_oos:
            is_oos = True
            if p1 < self.tau_oos and top_label != "out_of_scope":
                # When confidence falls below tau_oos, designate as out_of_scope / low confidence
                top_label = "out_of_scope"

        return ClassificationDecision(
            intent_label=top_label,
            confidence=p1,
            is_out_of_scope=is_oos,
            candidates=candidates,
            is_ambiguous_multi_issue=is_ambiguous,
            explanation_exemplar_ids=exemplar_ids or [f"ex-{top_label}-1", f"ex-{top_label}-2"],
        )

    def decide_from_logits(
        self,
        logits: list[float],
        top_k: int = 3,
        exemplar_ids: list[str] | None = None,
    ) -> ClassificationDecision:
        """Apply temperature scaling then evaluate decision rules."""
        calibrated_probs = softmax(logits, temperature=self.temperature)
        return self.decide_from_probabilities(
            calibrated_probs,
            top_k=top_k,
            exemplar_ids=exemplar_ids,
        )
