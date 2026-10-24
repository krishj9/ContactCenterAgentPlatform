"""Post-Training Temperature Scaling & Calibration (P4.4).

Fits optimal temperature parameter T > 0 on validation split logits using NLL minimization.
Computes Expected Calibration Error (ECE) across reliability bins.
"""

from __future__ import annotations

import math
from typing import Any


def softmax(logits: list[float], temperature: float = 1.0) -> list[float]:
    """Compute temperature-scaled softmax probabilities."""
    scaled = [x / max(1e-4, temperature) for x in logits]
    max_val = max(scaled)
    exp_vals = [math.exp(x - max_val) for x in scaled]
    sum_exp = sum(exp_vals)
    return [x / sum_exp for x in exp_vals]


class TemperatureScaler:
    """Post-training temperature scaling for sequence classification calibration."""

    def __init__(self, temperature: float = 1.0) -> None:
        self.temperature = float(temperature)

    def fit(
        self,
        val_logits: list[list[float]],
        val_labels: list[int],
        lr: float = 0.01,
        max_iters: int = 150,
        tol: float = 1e-4,
    ) -> float:
        """Fit temperature T on validation logits via gradient descent on negative log likelihood."""
        if not val_logits or not val_labels:
            self.temperature = 1.0
            return self.temperature

        # Optimize log(T) to ensure T > 0
        log_temp = math.log(max(1e-2, self.temperature))
        n_samples = len(val_labels)

        for _ in range(max_iters):
            temp = max(1e-2, min(10.0, math.exp(log_temp)))

            # Compute NLL loss and gradient w.r.t log_temp
            grad = 0.0
            for logits, true_label in zip(val_logits, val_labels, strict=False):
                probs = softmax(logits, temp)

                # d(NLL)/d(temp) = sum_j (p_j * (z_j - z_y)) / temp^2
                # d(temp)/d(log_temp) = temp
                # d(NLL)/d(log_temp) = sum_j (p_j * (z_j - z_y)) / temp
                true_logit = logits[true_label] if true_label < len(logits) else 0.0
                sample_grad = sum(
                    p * (z - true_logit) for p, z in zip(probs, logits, strict=False)
                ) / max(1e-3, temp)
                grad += sample_grad

            grad /= n_samples

            # Gradient step with gradient clipping
            grad = max(-5.0, min(5.0, grad))
            log_temp -= lr * grad
            if abs(grad) < tol:
                break

        self.temperature = max(0.1, min(5.0, math.exp(log_temp)))
        return self.temperature

    def scale_logits(self, logits: list[float]) -> list[float]:
        """Return temperature-scaled softmax probabilities."""
        return softmax(logits, self.temperature)


def compute_ece(
    confidences: list[float],
    accuracies: list[bool],
    num_bins: int = 10,
) -> dict[str, Any]:
    """Compute Expected Calibration Error (ECE) and binning statistics.

    ECE = sum_m (|B_m| / N) * |acc(B_m) - conf(B_m)|
    """
    if not confidences or not accuracies or len(confidences) != len(accuracies):
        return {"ece": 0.0, "bins": []}

    n = len(confidences)
    bin_size = 1.0 / num_bins
    bins_data: list[dict[str, Any]] = []
    total_weighted_diff = 0.0

    for i in range(num_bins):
        bin_lower = i * bin_size
        bin_upper = (i + 1) * bin_size

        indices = [
            idx
            for idx, c in enumerate(confidences)
            if (bin_lower <= c < bin_upper) or (i == num_bins - 1 and bin_lower <= c <= bin_upper)
        ]

        count = len(indices)
        if count > 0:
            avg_conf = sum(confidences[idx] for idx in indices) / count
            avg_acc = sum(1.0 for idx in indices if accuracies[idx]) / count
            abs_diff = abs(avg_acc - avg_conf)
            total_weighted_diff += (count / n) * abs_diff

            bins_data.append(
                {
                    "bin_index": i,
                    "bin_range": [round(bin_lower, 2), round(bin_upper, 2)],
                    "count": count,
                    "avg_confidence": round(avg_conf, 4),
                    "avg_accuracy": round(avg_acc, 4),
                    "calibration_gap": round(abs_diff, 4),
                }
            )
        else:
            bins_data.append(
                {
                    "bin_index": i,
                    "bin_range": [round(bin_lower, 2), round(bin_upper, 2)],
                    "count": 0,
                    "avg_confidence": 0.0,
                    "avg_accuracy": 0.0,
                    "calibration_gap": 0.0,
                }
            )

    return {
        "ece": round(total_weighted_diff, 5),
        "num_samples": n,
        "bins": bins_data,
    }
