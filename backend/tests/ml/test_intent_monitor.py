"""Unit Tests for Vertex AI Intent Model Monitoring & Drift Detection (Phase P9.7)."""

from __future__ import annotations

import pytest
from ml.monitoring.intent_monitor import (
    IntentModelMonitor,
    compute_jsd,
    compute_kl_divergence,
    compute_shannon_entropy,
)


def test_entropy_and_divergence_math_invariants() -> None:
    """Verify information theoretic mathematical properties:
    - Pure state entropy is 0.
    - Balanced binary entropy is 1 bit.
    - KL divergence of identical distributions is 0.
    - JSD is symmetric and bounded in [0, 1].
    """
    # Shannon Entropy
    assert compute_shannon_entropy([1.0, 0.0]) == pytest.approx(0.0, abs=1e-6)
    assert compute_shannon_entropy([0.5, 0.5]) == pytest.approx(1.0, abs=1e-6)

    # KL Divergence
    p = [0.7, 0.3]
    assert compute_kl_divergence(p, p) == pytest.approx(0.0, abs=1e-6)

    # JSD Symmetry and bounds
    q = [0.2, 0.8]
    jsd_pq = compute_jsd(p, q)
    jsd_qp = compute_jsd(q, p)
    assert jsd_pq == pytest.approx(jsd_qp, abs=1e-6)
    assert 0.0 <= jsd_pq <= 1.0


def test_intent_monitor_no_drift_on_conforming_traffic() -> None:
    """Verify monitor does not flag drift when production traffic matches baseline."""
    monitor = IntentModelMonitor(jsd_threshold=0.15, oov_threshold=0.20)

    # Conforming predictions matching canonical baseline
    conforming_predictions = (
        [{"label": "card_declined", "score": 0.95}] * 25
        + [{"label": "fee_dispute", "score": 0.92}] * 20
        + [{"label": "travel_notice", "score": 0.90}] * 15
        + [{"label": "lost_or_stolen_card", "score": 0.96}] * 15
        + [{"label": "charge_dispute", "score": 0.91}] * 15
        + [{"label": "out_of_scope", "score": 0.85}] * 10
    )

    pred_res = monitor.evaluate_prediction_drift(conforming_predictions)
    assert pred_res.drift_detected is False
    assert pred_res.jsd_divergence < 0.15

    # Conforming in-domain banking utterances
    banking_utterances = [
        "My card was declined at the grocery store atm",
        "Can you waive this monthly maintenance fee please",
        "I am submitting a travel notice for my trip",
        "My card is lost or stolen, please freeze it",
        "I want to dispute an unrecognized charge on my statement",
    ]
    input_res = monitor.evaluate_input_drift(banking_utterances)
    assert input_res.drift_detected is False
    assert input_res.oov_rate < 0.20

    # Overall report
    report = monitor.generate_report(conforming_predictions, banking_utterances)
    assert report.drift_detected is False
    assert report.requires_retraining is False
    assert len(report.reasons) == 0


def test_intent_monitor_detects_prediction_distribution_shift() -> None:
    """Verify monitor triggers drift alert when intent distribution skews heavily."""
    monitor = IntentModelMonitor(jsd_threshold=0.15)

    # 100% of traffic suddenly predicted as "out_of_scope" (extreme distribution shift)
    shifted_predictions = [{"label": "out_of_scope", "score": 0.95}] * 50

    pred_res = monitor.evaluate_prediction_drift(shifted_predictions)
    assert pred_res.drift_detected is True
    assert pred_res.jsd_divergence > 0.15

    report = monitor.generate_report(shifted_predictions, ["hello bank"])
    assert report.drift_detected is True
    assert report.requires_retraining is True
    assert any("JSD divergence" in r for r in report.reasons)


def test_intent_monitor_detects_vocabulary_drift() -> None:
    """Verify monitor triggers drift alert when user utterances contain novel out-of-vocabulary terms."""
    monitor = IntentModelMonitor(oov_threshold=0.20)

    # Utterances containing out-of-domain slang / topics
    novel_utterances = [
        "crypto bitcoin mining blockchain ethereum web3 staking yield",
        "quantum computing teleportation astrophysics galactic federation",
        "recipe cookbook spaghetti bolognese lasagna parmesan oregano",
    ]

    input_res = monitor.evaluate_input_drift(novel_utterances)
    assert input_res.drift_detected is True
    assert input_res.oov_rate > 0.20

    conforming_preds = [{"label": "card_declined", "score": 0.95}] * 10
    report = monitor.generate_report(conforming_preds, novel_utterances)
    assert report.drift_detected is True
    assert report.requires_retraining is True
    assert any("OOV rate" in r for r in report.reasons)
