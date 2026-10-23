"""Unit tests for corpus manifest and startup checks (P3.7)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.startup_checks import run_startup_checks
from pipeline.manifest import CorpusManifestManager


def test_build_and_verify_manifest() -> None:
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    manager = CorpusManifestManager(repo_root=repo_root)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_manifest = Path(tmp_dir) / "manifest.json"
        written_path = manager.write_manifest(
            dest_path=tmp_manifest,
            corpus_version="v1.0",
            embedder_model="EmbeddingGemma",
            embedding_dim=768,
        )
        assert written_path.exists()

        # Verification with matching config succeeds
        errors = manager.verify_runtime_compatibility(
            embedder_model="EmbeddingGemma",
            embedding_dim=768,
            manifest_path=tmp_manifest,
        )
        assert errors == []

        # Verification with mismatched dimension fails
        dim_errors = manager.verify_runtime_compatibility(
            embedder_model="EmbeddingGemma",
            embedding_dim=384,
            manifest_path=tmp_manifest,
        )
        assert len(dim_errors) == 1
        assert "dimension mismatch" in dim_errors[0]

        # Verification with mismatched model fails
        model_errors = manager.verify_runtime_compatibility(
            embedder_model="bert-base-uncased",
            embedding_dim=768,
            manifest_path=tmp_manifest,
        )
        assert len(model_errors) == 1
        assert "model mismatch" in model_errors[0]


def test_startup_checks_in_test_profile() -> None:
    # Test profile skips manifest checks
    settings = Settings(APP_PROFILE="test")
    run_startup_checks(settings)


def test_startup_checks_halts_on_mismatch() -> None:
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    manager = CorpusManifestManager(repo_root=repo_root)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_data = Path(tmp_dir)
        manager.write_manifest(
            dest_path=tmp_data / "manifest.json",
            corpus_version="v1.0",
            embedder_model="EmbeddingGemma",
            embedding_dim=768,
        )

        settings = Settings(
            APP_PROFILE="local",
            DATA_DIR=tmp_data,
            EMBEDDER_MODEL="MismatchedModel",
            EMBEDDING_DIM=768,
        )

        with pytest.raises(RuntimeError, match="Startup Pre-flight Check FAILED"):
            run_startup_checks(settings)
