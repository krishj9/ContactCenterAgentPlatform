"""Evaluation Harness for Intent Classifier (Spec §3.2.4, P4.5).

Computes accuracy, macro-F1, per-class F1, Expected Calibration Error (ECE),
OOS precision/recall curve, and p95 latency benchmark.
"""

from __future__ import annotations

import math
import time
from collections import defaultdict
from typing import Any

from ml.intent.calibrate import compute_ece


def calculate_metrics(
    predictions: list[str],
    ground_truths: list[str],
    confidences: list[float],
    in_scope_labels: set[str],
) -> dict[str, Any]:
    """Calculate accuracy, macro-F1, per-class F1, and ECE."""
    n = len(ground_truths)
    if n == 0:
        return {}

    correct = sum(1 for p, y in zip(predictions, ground_truths, strict=False) if p == y)
    accuracy = correct / n

    # Per-class counts
    tp: dict[str, int] = defaultdict(int)
    fp: dict[str, int] = defaultdict(int)
    fn: dict[str, int] = defaultdict(int)

    all_labels = sorted(set(ground_truths) | set(predictions))
    for p, y in zip(predictions, ground_truths, strict=False):
        if p == y:
            tp[y] += 1
        else:
            fp[p] += 1
            fn[y] += 1

    per_class_f1: dict[str, float] = {}
    for lbl in all_labels:
        true_pos = tp[lbl]
        false_pos = fp[lbl]
        false_neg = fn[lbl]
        precision = true_pos / (true_pos + false_pos) if (true_pos + false_pos) > 0 else 0.0
        recall = true_pos / (true_pos + false_neg) if (true_pos + false_neg) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        per_class_f1[lbl] = round(f1, 4)

    # In-scope Macro-F1
    in_scope_eval = [lbl for lbl in in_scope_labels if lbl in per_class_f1]
    if in_scope_eval:
        macro_f1 = sum(per_class_f1[lbl] for lbl in in_scope_eval) / len(in_scope_eval)
    else:
        macro_f1 = sum(per_class_f1.values()) / max(1, len(per_class_f1))

    # Calibration ECE
    accuracies = [p == y for p, y in zip(predictions, ground_truths, strict=False)]
    ece_result = compute_ece(confidences, accuracies, num_bins=10)

    # OOS Precision & Recall
    oos_tp = tp["out_of_scope"]
    oos_fp = fp["out_of_scope"]
    oos_fn = fn["out_of_scope"]
    oos_precision = oos_tp / (oos_tp + oos_fp) if (oos_tp + oos_fp) > 0 else 1.0
    oos_recall = oos_tp / (oos_tp + oos_fn) if (oos_tp + oos_fn) > 0 else 1.0

    in_scope_tp = sum(tp[lbl] for lbl in in_scope_labels)
    in_scope_fp = sum(fp[lbl] for lbl in in_scope_labels)
    in_scope_precision = (
        in_scope_tp / (in_scope_tp + in_scope_fp) if (in_scope_tp + in_scope_fp) > 0 else 0.0
    )

    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "ece": ece_result["ece"],
        "ece_details": ece_result,
        "oos_recall": round(oos_recall, 4),
        "oos_precision": round(oos_precision, 4),
        "in_scope_precision": round(in_scope_precision, 4),
        "per_class_f1": per_class_f1,
        "sample_count": n,
    }


def benchmark_latency(
    predict_fn: Any,
    sample_texts: list[str],
    iterations: int = 50,
) -> dict[str, float]:
    """Benchmark local CPU int8 inference latency percentiles."""
    latencies: list[float] = []

    # Warmup
    for text in sample_texts[:3]:
        predict_fn(text)

    for _ in range(iterations):
        for text in sample_texts[:10]:
            t0 = time.perf_counter()
            predict_fn(text)
            dt = (time.perf_counter() - t0) * 1000.0  # ms
            latencies.append(dt)

    latencies.sort()
    n = len(latencies)
    if n == 0:
        return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0, "mean": 0.0}

    def percentile(p: float) -> float:
        idx = min(n - 1, max(0, int(math.ceil(p * n)) - 1))
        return round(latencies[idx], 2)

    return {
        "p50": percentile(0.50),
        "p90": percentile(0.90),
        "p95": percentile(0.95),
        "p99": percentile(0.99),
        "mean": round(sum(latencies) / n, 2),
    }
