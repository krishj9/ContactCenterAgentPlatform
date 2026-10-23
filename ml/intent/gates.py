"""Quality Gate Verification for Intent Classifier Release (Spec §3.2.4).

Asserts all release thresholds before registering or promoting an intent model.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GateCheck:
    """Individual quality gate metric check."""

    name: str
    target: str
    actual: float
    passed: bool
    description: str


@dataclass
class QualityGateResult:
    """Overall release decision with gate breakdown."""

    passed: bool
    checks: list[GateCheck] = field(default_factory=list)
    failure_reasons: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [f"Quality Gate Status: {'PASSED' if self.passed else 'FAILED'}"]
        for c in self.checks:
            mark = "✓" if c.passed else "✗"
            lines.append(f"  [{mark}] {c.name}: actual={c.actual} (target: {c.target}) - {c.description}")
        return "\n".join(lines)


def evaluate_quality_gates(
    report: dict[str, Any],
    golden_scenario_accuracy: float,
    latency_p95_ms: float,
    high_risk_labels: list[str] | None = None,
) -> QualityGateResult:
    """Evaluate full set of Spec §3.2.4 champion quality gates."""
    checks: list[GateCheck] = []
    failures: list[str] = []

    # 1. Test Accuracy >= 0.93
    acc = float(report.get("accuracy", 0.0))
    acc_pass = acc >= 0.93
    checks.append(GateCheck("Test Accuracy", ">= 0.93", acc, acc_pass, "Overall test accuracy"))
    if not acc_pass:
        failures.append(f"Accuracy {acc:.4f} is below target 0.93")

    # 2. Macro-F1 >= 0.92
    macro_f1 = float(report.get("macro_f1", 0.0))
    f1_pass = macro_f1 >= 0.92
    checks.append(GateCheck("Macro-F1", ">= 0.92", macro_f1, f1_pass, "In-scope macro-F1"))
    if not f1_pass:
        failures.append(f"Macro-F1 {macro_f1:.4f} is below target 0.92")

    # 3. ECE <= 0.05
    ece = float(report.get("ece", 1.0))
    ece_pass = ece <= 0.05
    checks.append(GateCheck("ECE", "<= 0.05", ece, ece_pass, "Expected Calibration Error"))
    if not ece_pass:
        failures.append(f"ECE {ece:.4f} is above target 0.05")

    # 4. OOS Recall >= 0.85
    oos_rec = float(report.get("oos_recall", 0.0))
    oos_pass = oos_rec >= 0.85
    checks.append(GateCheck("OOS Recall", ">= 0.85", oos_rec, oos_pass, "Out-of-scope recall"))
    if not oos_pass:
        failures.append(f"OOS Recall {oos_rec:.4f} is below target 0.85")

    # 5. In-scope Precision >= 0.95
    in_scope_prec = float(report.get("in_scope_precision", 0.0))
    prec_pass = in_scope_prec >= 0.95
    checks.append(GateCheck("In-scope Precision", ">= 0.95", in_scope_prec, prec_pass, "In-scope precision"))
    if not prec_pass:
        failures.append(f"In-scope Precision {in_scope_prec:.4f} is below target 0.95")

    # 6. High-Risk per-class F1 >= 0.75
    per_class_f1 = report.get("per_class_f1", {})
    high_risk = high_risk_labels or ["fraud_report", "lost_or_stolen_card", "card_declined"]
    high_risk_failures = []
    min_high_risk_f1 = 1.0
    for lbl in high_risk:
        score = per_class_f1.get(lbl, 1.0)
        min_high_risk_f1 = min(min_high_risk_f1, score)
        if score < 0.75:
            high_risk_failures.append(f"{lbl}={score:.4f}")

    hr_pass = len(high_risk_failures) == 0
    checks.append(GateCheck(
        "High-Risk F1",
        ">= 0.75",
        round(min_high_risk_f1, 4),
        hr_pass,
        f"Minimum F1 across high risk labels ({', '.join(high_risk)})",
    ))
    if not hr_pass:
        failures.append(f"High risk intents below F1 0.75: {', '.join(high_risk_failures)}")

    # 7. Golden Scenario Top-1 Accuracy == 100%
    scenario_pass = golden_scenario_accuracy >= 1.0
    checks.append(GateCheck(
        "Golden Scenario Accuracy",
        "== 1.00",
        round(golden_scenario_accuracy, 4),
        scenario_pass,
        "Top-1 accuracy on golden scenario turns",
    ))
    if not scenario_pass:
        failures.append(f"Golden scenario accuracy {golden_scenario_accuracy:.4f} is not 100%")

    # 8. Local CPU p95 Latency <= 250ms
    latency_pass = latency_p95_ms <= 250.0
    checks.append(GateCheck(
        "Local CPU p95 Latency",
        "<= 250.0 ms",
        round(latency_p95_ms, 2),
        latency_pass,
        "Local CPU int8 inference latency percentile p95",
    ))
    if not latency_pass:
        failures.append(f"Latency p95 {latency_p95_ms:.2f}ms exceeds 250ms limit")

    passed_all = len(failures) == 0
    return QualityGateResult(
        passed=passed_all,
        checks=checks,
        failure_reasons=failures,
    )
