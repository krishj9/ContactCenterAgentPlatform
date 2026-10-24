"""Unit Tests for Nightly GenAI Quality Evaluation Job (Phase P9.6)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval.jobs.nightly import NightlyAuditReport, run_nightly_quality_audit

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@pytest.mark.asyncio
async def test_nightly_audit_passes_on_golden_scenarios(tmp_path: Path) -> None:
    """Verify nightly audit executes across golden scenarios and meets exit targets:
    - Groundedness >= 0.90
    - Intent accuracy == 100%
    """
    scenarios_dir = _REPO_ROOT / "eval" / "scenarios"
    output_report = tmp_path / "nightly_report.json"

    report: NightlyAuditReport = await run_nightly_quality_audit(
        scenarios_dir=scenarios_dir,
        output_report_path=output_report,
        groundedness_target=0.90,
    )

    assert report.total_scenarios >= 3
    assert report.intent_accuracy == 1.0, f"Expected 100% accuracy, got {report.intent_accuracy}"
    assert report.mean_groundedness_score >= 0.90, (
        f"Groundedness {report.mean_groundedness_score} is below 0.90"
    )
    assert report.passed is True
    assert len(report.failure_reasons) == 0

    # Verify JSON report file was written
    assert output_report.exists()
    with open(output_report, encoding="utf-8") as f:
        data = json.load(f)
    assert data["passed"] is True
    assert data["mean_groundedness_score"] >= 0.90
    assert data["intent_accuracy"] == 1.0


@pytest.mark.asyncio
async def test_nightly_audit_detects_unmet_groundedness_target() -> None:
    """Verify that if groundedness target is higher than achieved score, job fails with clear diagnostic."""
    scenarios_dir = _REPO_ROOT / "eval" / "scenarios"

    # Set an impossible target (1.05) to test exit gate enforcement
    report = await run_nightly_quality_audit(
        scenarios_dir=scenarios_dir,
        groundedness_target=1.05,
    )

    assert report.passed is False
    assert any("below exit target" in reason for reason in report.failure_reasons)


@pytest.mark.asyncio
async def test_nightly_audit_empty_directory_raises(tmp_path: Path) -> None:
    """Verify error is raised when scenario fixtures directory is empty."""
    empty_dir = tmp_path / "empty_scenarios"
    empty_dir.mkdir()

    with pytest.raises(FileNotFoundError, match="No scenario JSON fixtures found"):
        await run_nightly_quality_audit(scenarios_dir=empty_dir)
