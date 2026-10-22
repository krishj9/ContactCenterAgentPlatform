"""Unit tests for CorpusPaths and settings configuration."""

from pathlib import Path

from app.core.config import Settings, get_settings
from app.pipeline.paths import CorpusPaths


def test_corpus_paths_directory_structure(tmp_path: Path):
    """Test CorpusPaths resolves standard medallion directory structure."""
    paths = CorpusPaths(root_dir=tmp_path)
    assert paths.raw_dir == tmp_path / "raw"
    assert paths.processed_dir == tmp_path / "processed"
    assert paths.normalized_dir == tmp_path / "processed" / "normalized"
    assert paths.chunks_dir == tmp_path / "processed" / "chunks"
    assert paths.quarantine_dir == tmp_path / "quarantine"
    assert paths.embeddings_dir == tmp_path / "embeddings"

    paths.ensure_dirs()
    assert paths.raw_dir.is_dir()
    assert paths.normalized_dir.is_dir()
    assert paths.chunks_dir.is_dir()
    assert paths.quarantine_dir.is_dir()


def test_corpus_paths_filenames(tmp_path: Path):
    """Test CorpusPaths resolves specific store filenames."""
    paths = CorpusPaths(root_dir=tmp_path)
    raw_b77 = paths.raw_path("banking77", "train.csv")
    assert raw_b77 == tmp_path / "raw" / "banking77" / "train.csv"

    norm_faq = paths.normalized_path("faq")
    assert norm_faq == tmp_path / "processed" / "normalized" / "faq" / "faq.normalized.jsonl"

    chunks_policy = paths.chunks_path("policy", "v1")
    assert (
        chunks_policy == tmp_path / "processed" / "chunks" / "policy" / "v1" / "policy.chunks.jsonl"
    )


def test_max_records_per_store_default_unlimited():
    """Verify MAX_RECORDS_PER_STORE defaults to 0 (unlimited), addressing Finding F3."""
    settings = Settings()
    assert settings.MAX_RECORDS_PER_STORE == 0
    cached = get_settings()
    assert cached.MAX_RECORDS_PER_STORE == 0
