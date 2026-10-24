"""Unit & Integration Tests for Model Promotion & Canary Rollback (Phase P8.2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from ml.pipelines.promote_intent import (
    CanaryRollbackException,
    promote_intent_model,
)


@pytest.fixture
def staged_artifacts_dir(tmp_path: Path) -> Path:
    """Fixture creating mock Model Registry state with challenger and champion."""
    artifacts_dir = tmp_path / "artifacts"
    registry_dir = artifacts_dir / "registry"
    registry_dir.mkdir(parents=True)

    # Initial champion model
    champion_metadata = {
        "model_id": "intent-gemma3-1b-lora@champion-v1",
        "alias": "champion",
        "taxonomy_version": "tx-14",
        "accuracy": 0.941,
    }
    with open(registry_dir / "champion.json", "w", encoding="utf-8") as f:
        json.dump(champion_metadata, f, indent=2)

    # Candidate challenger model
    challenger_metadata = {
        "model_id": "intent-gemma3-1b-lora@challenger-v2",
        "alias": "challenger",
        "taxonomy_version": "tx-14",
        "accuracy": 0.948,
    }
    with open(registry_dir / "challenger.json", "w", encoding="utf-8") as f:
        json.dump(challenger_metadata, f, indent=2)

    return artifacts_dir


def test_promote_intent_model_success_lifecycle(staged_artifacts_dir: Path) -> None:
    """Verify progressive canary rollout (10% -> 50% -> 100%) and champion alias promotion."""
    result = promote_intent_model(
        artifacts_dir=staged_artifacts_dir,
        endpoint_id="intent-endpoint-prod",
        simulate_failure=False,
    )

    assert result.promoted is True
    assert result.new_champion_id == "intent-gemma3-1b-lora@challenger-v2"
    assert result.previous_champion_id == "intent-gemma3-1b-lora@champion-v1"
    assert result.final_traffic == {"intent-gemma3-1b-lora@challenger-v2": 100}

    expected_stages = [
        "canary_10_percent_verified",
        "canary_50_percent_verified",
        "cutover_100_percent_verified",
        "alias_champion_promoted",
    ]
    assert result.stages_completed == expected_stages

    # Verify updated champion.json
    registry_dir = staged_artifacts_dir / "registry"
    with open(registry_dir / "champion.json", encoding="utf-8") as f:
        champ_data = json.load(f)
    assert champ_data["alias"] == "champion"
    assert champ_data["model_id"] == "intent-gemma3-1b-lora@challenger-v2"

    # Verify previous_champion.json was archived
    with open(registry_dir / "previous_champion.json", encoding="utf-8") as f:
        prev_data = json.load(f)
    assert prev_data["model_id"] == "intent-gemma3-1b-lora@champion-v1"

    # Verify endpoint_state.json shows 100% cutover
    with open(staged_artifacts_dir / "endpoint_state.json", encoding="utf-8") as f:
        state = json.load(f)
    assert state["traffic_split"]["intent-gemma3-1b-lora@challenger-v2"] == 100
    assert state["canary_status"] == "promoted"


def test_promote_intent_model_automated_rollback_on_canary_failure(
    staged_artifacts_dir: Path,
) -> None:
    """Verify automated rollback when canary probe encounters errors/latency spike."""
    with pytest.raises(CanaryRollbackException, match="Canary.*failed"):
        promote_intent_model(
            artifacts_dir=staged_artifacts_dir,
            endpoint_id="intent-endpoint-prod",
            simulate_failure=True,  # Triggers simulated health check failure
        )

    # Assert endpoint state was transactionally rolled back
    state_file = staged_artifacts_dir / "endpoint_state.json"
    assert state_file.exists()
    with open(state_file, encoding="utf-8") as f:
        state = json.load(f)

    assert state["canary_status"] == "rolled_back"
    # Traffic must be restored 100% to champion and 0% to challenger
    assert state["traffic_split"]["intent-gemma3-1b-lora@champion-v1"] == 100
    assert state["traffic_split"]["intent-gemma3-1b-lora@challenger-v2"] == 0

    # Ensure champion was NOT replaced
    registry_dir = staged_artifacts_dir / "registry"
    with open(registry_dir / "champion.json", encoding="utf-8") as f:
        champ_data = json.load(f)
    assert champ_data["model_id"] == "intent-gemma3-1b-lora@champion-v1"


def test_promote_intent_model_missing_challenger_raises_error(tmp_path: Path) -> None:
    """Verify attempting to promote when no challenger exists raises FileNotFoundError."""
    empty_artifacts = tmp_path / "artifacts"
    empty_artifacts.mkdir()
    (empty_artifacts / "registry").mkdir()

    with pytest.raises(FileNotFoundError, match="No candidate model found"):
        promote_intent_model(artifacts_dir=empty_artifacts)
