"""Corpus paths and data directory management."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field


class CorpusPaths(BaseModel):
    """Centralized, deterministic path resolver for all corpus layers."""

    root_dir: Path = Field(default_factory=lambda: Path(os.getenv("CC_DATA_DIR", "data")))

    model_config = {"arbitrary_types_allowed": True}

    @property
    def raw_dir(self) -> Path:
        return self.root_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.root_dir / "processed"

    @property
    def normalized_dir(self) -> Path:
        return self.processed_dir / "normalized"

    @property
    def chunks_dir(self) -> Path:
        return self.processed_dir / "chunks"

    @property
    def quarantine_dir(self) -> Path:
        return self.root_dir / "quarantine"

    @property
    def embeddings_dir(self) -> Path:
        return self.root_dir / "embeddings"

    def raw_path(self, store: str, filename: str) -> Path:
        """Return path to a raw source file: data/raw/{store}/{filename}."""
        return self.raw_dir / store / filename

    def normalized_path(self, store: str, corpus_version: str | None = None) -> Path:
        """Return path to normalized jsonl file.

        Canonical path: data/processed/normalized/{store}/{store}.normalized.jsonl
        (or with version: data/processed/normalized/{store}/{corpus_version}/{store}.normalized.jsonl)
        Also resolves legacy paths if existing.
        """
        if corpus_version:
            target = self.normalized_dir / store / corpus_version / f"{store}.normalized.jsonl"
        else:
            target = self.normalized_dir / store / f"{store}.normalized.jsonl"

        # Check legacy fallback paths when reading
        legacy_nested = self.processed_dir / store / f"{store}.normalized.jsonl"
        legacy_flat = self.processed_dir / f"{store}.normalized.jsonl"

        if not target.exists():
            if legacy_nested.exists():
                return legacy_nested
            if legacy_flat.exists():
                return legacy_flat

        return target

    def chunks_path(self, store: str, corpus_version: str | None = None) -> Path:
        """Return path to chunked jsonl file."""
        if corpus_version:
            return self.chunks_dir / store / corpus_version / f"{store}.chunks.jsonl"
        return self.chunks_dir / store / f"{store}.chunks.jsonl"

    def quarantine_path(self, store: str, filename: str) -> Path:
        """Return path to quarantined records."""
        return self.quarantine_dir / store / filename

    def ensure_dirs(self) -> None:
        """Create all data directories if they do not exist."""
        for directory in [
            self.raw_dir,
            self.processed_dir,
            self.normalized_dir,
            self.chunks_dir,
            self.quarantine_dir,
            self.embeddings_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)
