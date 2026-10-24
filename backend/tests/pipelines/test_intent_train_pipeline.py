"""Unit & Integration Tests for KFP Intent Classifier Pipeline (Phase P8.1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from ml.pipelines.intent_train import (
    compile_pipeline,
    run_intent_training_pipeline,
    validate_splits,
)


def test_compile_kfp_v2_intent_spec(tmp_path: Path) -> None:
    """Verify KFP v2 pipeline definition compiles and contains all Spec §3.2.4 tasks."""
    spec_file = tmp_path / "test_pipeline.json"
    compile_pipeline(spec_file)

    assert spec_file.exists()
    with open(spec_file, encoding="utf-8") as f:
        spec = json.load(f)

    assert spec["schemaVersion"] == "2.1.0"
    tasks = spec["root"]["dag"]["tasks"]
    expected_tasks = [
        "data-prep",
        "validate-data",
        "train-lora",
        "calibrate-temperature",
        "evaluate-gates",
        "register-challenger",
    ]
    for task_name in expected_tasks:
        assert task_name in tasks, f"Missing expected KFP task: {task_name}"

    # Verify task lineage / dependencies
    assert tasks["register-challenger"]["dependentTasks"] == ["evaluate-gates"]
    assert tasks["evaluate-gates"]["dependentTasks"] == ["calibrate-temperature"]


def test_validate_splits_valid(tmp_path: Path) -> None:
    """Verify schema validation and zero leakage assertion on valid dataset."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    taxonomy_path = repo_root / "taxonomy" / "intents.yaml"

    train_data = [
        {"text": "why was my card declined at the store", "intent": "card_declined"},
        {"text": "i need to waive this late fee", "intent": "fee_dispute"},
    ]
    val_data = [
        {"text": "can you remove this penalty charge", "intent": "fee_dispute"},
    ]
    test_data = [
        {"text": "card was rejected when paying dinner", "intent": "card_declined"},
    ]

    for name, items in [
        ("train.jsonl", train_data),
        ("val.jsonl", val_data),
        ("test.jsonl", test_data),
    ]:
        with open(data_dir / name, "w", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it) + "\n")

    stats = validate_splits(data_dir, taxonomy_path)
    assert stats["status"] == "PASSED"
    assert stats["train_count"] == 2
    assert stats["val_count"] == 1
    assert stats["test_count"] == 1


def test_validate_splits_detects_data_leakage(tmp_path: Path) -> None:
    """Verify data leakage assertion raises exception when utterance overlaps across splits."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    taxonomy_path = repo_root / "taxonomy" / "intents.yaml"

    leaked_text = "card declined at restaurant"
    train_data = [{"text": leaked_text, "intent": "card_declined"}]
    val_data = [{"text": "waive fee please", "intent": "fee_dispute"}]
    test_data = [{"text": leaked_text, "intent": "card_declined"}]  # Leakage!

    for name, items in [
        ("train.jsonl", train_data),
        ("val.jsonl", val_data),
        ("test.jsonl", test_data),
    ]:
        with open(data_dir / name, "w", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it) + "\n")

    with pytest.raises(ValueError, match="Data leakage detected"):
        validate_splits(data_dir, taxonomy_path)


def test_intent_training_pipeline_executes_and_registers_challenger(tmp_path: Path) -> None:
    """Execute end-to-end intent training pipeline and verify challenger registration."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    config_path = repo_root / "ml" / "intent" / "configs" / "dev.yaml"
    out_dir = tmp_path / "artifacts"

    artifacts = run_intent_training_pipeline(
        config_path=config_path,
        output_dir=out_dir,
        skip_prep=False,
    )

    assert artifacts.quality_gates_passed is True
    assert artifacts.model_alias == "challenger"
    assert artifacts.golden_accuracy == 1.0
    assert artifacts.latency_p95_ms <= 250.0  # Local CPU latency gate

    # Verify registry metadata artifact
    registry_file = Path(artifacts.registry_uri)
    assert registry_file.exists()
    with open(registry_file, encoding="utf-8") as f:
        reg_data = json.load(f)

    assert reg_data["alias"] == "challenger"
    assert reg_data["taxonomy_version"] == "tx-14"
    assert reg_data["quality_gates_passed"] is True
