"""Unit & Integration Tests for Knowledge Base Pipeline (Phase P8.3)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from ml.pipelines.kb_build import (
    RetrievalQualityGateError,
    compile_pipeline,
    evaluate_retrieval_gates,
    run_kb_build_pipeline,
)


def test_compile_kfp_v2_kb_spec(tmp_path: Path) -> None:
    """Verify KFP v2 pipeline definition compiles and contains all KB build DAG tasks."""
    spec_file = tmp_path / "test_kb_pipeline.json"
    compile_pipeline(spec_file)

    assert spec_file.exists()
    with open(spec_file, encoding="utf-8") as f:
        spec = json.load(f)

    assert spec["schemaVersion"] == "2.1.0"
    tasks = spec["root"]["dag"]["tasks"]
    expected_tasks = [
        "ingest-and-chunk",
        "embed-and-stage-index",
        "retrieval-quality-gate",
        "promote-active-version",
    ]
    for task_name in expected_tasks:
        assert task_name in tasks, f"Missing expected KFP task: {task_name}"

    assert tasks["promote-active-version"]["dependentTasks"] == ["retrieval-quality-gate"]
    assert tasks["retrieval-quality-gate"]["dependentTasks"] == ["embed-and-stage-index"]


def test_evaluate_retrieval_gates_success() -> None:
    """Verify retrieval evaluation satisfies Phase P3 and P8 quality thresholds."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    qrels_path = repo_root / "eval" / "retrieval" / "qrels.jsonl"

    metrics = evaluate_retrieval_gates(
        qrels_path=qrels_path,
        target_version="v_test",
        recall_threshold=0.95,
        ndcg_threshold=0.85,
        simulate_failure=False,
    )

    assert metrics.gate_passed is True
    assert metrics.recall_at_20 >= 0.95
    assert metrics.ndcg_at_5 >= 0.85
    assert len(metrics.failure_reasons) == 0


def test_evaluate_retrieval_gates_failure_detection() -> None:
    """Verify retrieval quality gate catches degradation and blocks promotion."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    qrels_path = repo_root / "eval" / "retrieval" / "qrels.jsonl"

    metrics = evaluate_retrieval_gates(
        qrels_path=qrels_path,
        target_version="v_test_fail",
        recall_threshold=0.95,
        ndcg_threshold=0.85,
        simulate_failure=True,
    )

    assert metrics.gate_passed is False
    assert metrics.recall_at_20 < 0.95
    assert len(metrics.failure_reasons) >= 1


@pytest.mark.asyncio
async def test_run_kb_build_pipeline_gate_failure_aborts_promotion() -> None:
    """Verify quality gate failure raises RetrievalQualityGateError and aborts promotion."""
    with pytest.raises(RetrievalQualityGateError, match="Retrieval gate failed"):
        await run_kb_build_pipeline(
            target_version="v_fail_test",
            simulate_failure=True,
        )


@pytest.mark.asyncio
async def test_run_kb_build_pipeline_success(tmp_path: Path) -> None:
    """Verify end-to-end KB build, retrieval gate validation, and promotion report generation."""
    report_file = tmp_path / "kb_report.json"
    result = await run_kb_build_pipeline(
        target_version="v_test_promote",
        output_report_path=report_file,
        simulate_failure=False,
    )

    assert result["status"] == "PROMOTED"
    assert result["active_version"] == "v_test_promote"
    assert result["policy_chunks"] > 0
    assert result["retrieval_gates"]["gate_passed"] is True

    assert report_file.exists()
    with open(report_file, encoding="utf-8") as f:
        saved_report = json.load(f)
    assert saved_report["active_version"] == "v_test_promote"
