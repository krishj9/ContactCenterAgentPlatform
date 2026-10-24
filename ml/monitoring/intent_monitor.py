"""Vertex AI Model Monitoring & Intent Drift Detection (Spec §5.4, Phase P9.7).

Monitors production inference traffic on the intent classification endpoint for:
1. Prediction Drift: Shannon entropy H(p) and Jensen-Shannon Divergence (JSD) against baseline.
2. Input Drift: Vocabulary distribution shift, Out-of-Vocabulary (OOV) rate, and utterance length shift.
3. Automated Retraining Triggers: Flags DRIFT_DETECTED when JSD > 0.15 or OOV > 0.20.
"""

from __future__ import annotations

import argparse
import logging
import math
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Ensure workspace root is in sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

logger = logging.getLogger("ml.monitoring.intent_monitor")


def compute_shannon_entropy(probabilities: list[float]) -> float:
    """Compute Shannon entropy in bits: H(p) = -sum(p * log2(p))."""
    entropy = 0.0
    for p in probabilities:
        if p > 1e-9:
            entropy -= p * math.log2(p)
    return entropy


def compute_kl_divergence(p: list[float], q: list[float]) -> float:
    """Compute Kullback-Leibler divergence D_KL(P || Q)."""
    eps = 1e-9
    kl = 0.0
    for p_i, q_i in zip(p, q, strict=False):
        p_val = max(p_i, eps)
        q_val = max(q_i, eps)
        kl += p_val * math.log2(p_val / q_val)
    return kl


def compute_jsd(p: list[float], q: list[float]) -> float:
    """Compute symmetric bounded Jensen-Shannon Divergence JSD(P || Q) in [0, 1]."""
    m = [0.5 * (p_i + q_i) for p_i, q_i in zip(p, q, strict=False)]
    return 0.5 * compute_kl_divergence(p, m) + 0.5 * compute_kl_divergence(q, m)


@dataclass
class PredictionDriftResult:
    """Metrics assessing shifts in predicted intent distribution and confidence entropy."""

    mean_entropy: float
    jsd_divergence: float
    drift_detected: bool
    top_predicted_intents: dict[str, float]
    details: str


@dataclass
class InputDriftResult:
    """Metrics assessing linguistic, vocabulary, and length shifts in user input."""

    mean_token_length: float
    oov_rate: float
    drift_detected: bool
    vocabulary_size: int
    details: str


@dataclass
class ModelMonitoringReport:
    """Complete drift assessment and automated alerting output."""

    drift_detected: bool
    requires_retraining: bool
    prediction_drift: PredictionDriftResult
    input_drift: InputDriftResult
    sample_size: int
    timestamp: str
    reasons: list[str] = field(default_factory=list)


class IntentModelMonitor:
    """Monitors live intent inference traffic for distribution and vocabulary drift."""

    def __init__(
        self,
        baseline_intent_distribution: dict[str, float] | None = None,
        baseline_vocabulary: set[str] | None = None,
        jsd_threshold: float = 0.15,
        entropy_threshold: float = 2.20,
        oov_threshold: float = 0.20,
    ) -> None:
        self.jsd_threshold = jsd_threshold
        self.entropy_threshold = entropy_threshold
        self.oov_threshold = oov_threshold

        # Default reference distribution across canonical banking categories
        self.baseline_distribution = baseline_intent_distribution or {
            "card_declined": 0.25,
            "fee_dispute": 0.20,
            "travel_notice": 0.15,
            "lost_or_stolen_card": 0.15,
            "charge_dispute": 0.15,
            "out_of_scope": 0.10,
        }

        self.baseline_vocabulary = baseline_vocabulary or {
            "card",
            "declined",
            "fee",
            "waive",
            "travel",
            "notice",
            "lost",
            "stolen",
            "charge",
            "dispute",
            "payment",
            "atm",
            "transaction",
            "bank",
            "account",
            "balance",
            "statement",
            "refund",
            "pin",
            "blocked",
            "help",
            "fraud",
            "the",
            "and",
            "for",
            "with",
            "that",
            "this",
            "from",
            "are",
            "was",
            "were",
            "can",
            "could",
            "would",
            "will",
            "may",
            "you",
            "your",
            "our",
            "before",
            "after",
            "please",
            "once",
            "we",
            "all",
            "not",
            "have",
            "has",
            "had",
            "been",
            "my",
            "me",
            "at",
            "to",
            "in",
            "on",
            "is",
            "it",
            "so",
            "do",
            "does",
            "did",
            "grocery",
            "store",
            "trip",
            "freeze",
            "twice",
            "unrecognized",
            "monthly",
            "maintenance",
            "submit",
            "submitting",
            "want",
            "like",
            "need",
            "call",
            "agent",
        }

    def tokenize(self, text: str) -> list[str]:
        """Simple alphanumeric tokenizer."""
        return [w.lower() for w in re.findall(r"\b\w{2,}\b", text)]

    def evaluate_prediction_drift(self, predictions: list[dict[str, Any]]) -> PredictionDriftResult:
        """Measure prediction entropy and JSD against reference baseline."""
        if not predictions:
            return PredictionDriftResult(0.0, 0.0, False, {}, "No predictions evaluated.")

        # 1. Prediction entropy
        entropies = []
        class_counts: Counter[str] = Counter()

        for pred in predictions:
            # Score distribution across candidates or top prediction
            scores = pred.get("scores")
            if isinstance(scores, list) and len(scores) > 1:
                entropies.append(compute_shannon_entropy(scores))
            else:
                top_score = float(pred.get("score", 0.90))
                entropies.append(compute_shannon_entropy([top_score, max(0.0, 1.0 - top_score)]))

            label = pred.get("label", "out_of_scope")
            class_counts[label] += 1

        mean_entropy = sum(entropies) / len(entropies)

        # 2. Compute empirical probability vector over known categories
        all_categories = sorted(self.baseline_distribution.keys())
        total_preds = sum(class_counts.values())

        empirical_p = [class_counts.get(cat, 0) / total_preds for cat in all_categories]
        baseline_q = [self.baseline_distribution.get(cat, 0.001) for cat in all_categories]

        # Normalize baseline_q
        q_sum = sum(baseline_q)
        baseline_q = [val / q_sum for val in baseline_q]

        jsd = compute_jsd(empirical_p, baseline_q)

        drift = (jsd > self.jsd_threshold) or (mean_entropy > self.entropy_threshold)
        top_intents = {k: round(v / total_preds, 4) for k, v in class_counts.most_common(5)}

        return PredictionDriftResult(
            mean_entropy=round(mean_entropy, 4),
            jsd_divergence=round(jsd, 4),
            drift_detected=drift,
            top_predicted_intents=top_intents,
            details=f"Mean Entropy={mean_entropy:.3f} (limit {self.entropy_threshold}), JSD={jsd:.3f} (limit {self.jsd_threshold})",
        )

    def evaluate_input_drift(self, utterances: list[str]) -> InputDriftResult:
        """Measure OOV token rate and token length shift."""
        if not utterances:
            return InputDriftResult(0.0, 0.0, False, 0, "No utterances evaluated.")

        lengths = []
        oov_tokens = 0
        total_tokens = 0
        observed_vocab: set[str] = set()

        for u in utterances:
            tokens = self.tokenize(u)
            lengths.append(len(tokens))
            total_tokens += len(tokens)
            for t in tokens:
                observed_vocab.add(t)
                if t not in self.baseline_vocabulary:
                    oov_tokens += 1

        mean_len = sum(lengths) / len(lengths)
        oov_rate = oov_tokens / total_tokens if total_tokens > 0 else 0.0

        drift = oov_rate > self.oov_threshold

        return InputDriftResult(
            mean_token_length=round(mean_len, 2),
            oov_rate=round(oov_rate, 4),
            drift_detected=drift,
            vocabulary_size=len(observed_vocab),
            details=f"OOV rate={oov_rate:.2%} (limit {self.oov_threshold:.0%}), Mean Length={mean_len:.1f} words",
        )

    def generate_report(
        self,
        predictions: list[dict[str, Any]],
        utterances: list[str],
    ) -> ModelMonitoringReport:
        """Generate comprehensive drift report."""
        pred_drift = self.evaluate_prediction_drift(predictions)
        input_drift = self.evaluate_input_drift(utterances)

        reasons: list[str] = []
        if pred_drift.jsd_divergence > self.jsd_threshold:
            reasons.append(
                f"Prediction JSD divergence ({pred_drift.jsd_divergence:.4f}) exceeds threshold ({self.jsd_threshold})"
            )
        if pred_drift.mean_entropy > self.entropy_threshold:
            reasons.append(
                f"Prediction entropy ({pred_drift.mean_entropy:.4f}) indicates elevated classifier uncertainty"
            )
        if input_drift.oov_rate > self.oov_threshold:
            reasons.append(
                f"Input vocabulary OOV rate ({input_drift.oov_rate:.2%}) indicates new conversational terms"
            )

        drift_flag = pred_drift.drift_detected or input_drift.drift_detected

        return ModelMonitoringReport(
            drift_detected=drift_flag,
            requires_retraining=drift_flag,
            prediction_drift=pred_drift,
            input_drift=input_drift,
            sample_size=max(len(predictions), len(utterances)),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            reasons=reasons,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Intent Classifier Model Drift Monitor")
    parser.add_argument("--sample-size", type=int, default=50, help="Simulated sample size")
    parser.add_argument("--simulate-drift", action="store_true", help="Simulate input drift")
    args = parser.parse_args()

    monitor = IntentModelMonitor()
    if args.simulate_drift:
        utterances = [
            "crypto arbitrage bitcoin token swap metamask gas fee" for _ in range(args.sample_size)
        ]
        predictions = [{"label": "out_of_scope", "score": 0.45} for _ in range(args.sample_size)]
    else:
        utterances = [
            "my credit card was declined at grocery store" for _ in range(args.sample_size)
        ]
        predictions = [{"label": "card_declined", "score": 0.94} for _ in range(args.sample_size)]

    report = monitor.generate_report(predictions, utterances)
    print("\n" + "=" * 50)
    print("VERTEX AI MODEL MONITORING REPORT")
    print("=" * 50)
    print(f"Drift Detected: {report.drift_detected}")
    print(f"Prediction Details: {report.prediction_drift.details}")
    print(f"Input Details:      {report.input_drift.details}")
    if report.reasons:
        print("\nAlert Reasons:")
        for r in report.reasons:
            print(f"  - {r}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
