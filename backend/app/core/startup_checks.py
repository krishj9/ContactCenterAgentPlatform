"""Application Startup Health and Manifest Verification Checks (P3.7).

Halts server startup if runtime embedding model configuration is incompatible
with the indexed corpus metadata in data/manifest.json.
"""

from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import Settings
from pipeline.manifest import CorpusManifestManager

logger = logging.getLogger(__name__)


def run_startup_checks(settings: Settings) -> None:
    """Execute pre-flight environment and corpus consistency assertions."""
    if settings.APP_PROFILE == "test":
        logger.info("Running in test profile — skipping corpus manifest check.")
        return

    manifest_path = settings.DATA_DIR / "manifest.json"
    if not manifest_path.exists():
        logger.warning(
            f"Corpus manifest not found at {manifest_path}. If running a live environment, run 'make seed'."
        )
        return

    manager = CorpusManifestManager(repo_root=Path(__file__).resolve().parent.parent.parent.parent)
    errors = manager.verify_runtime_compatibility(
        embedder_model=settings.EMBEDDER_MODEL,
        embedding_dim=settings.EMBEDDING_DIM,
        manifest_path=manifest_path,
    )

    if errors:
        error_msg = "Startup Pre-flight Check FAILED:\n" + "\n".join(f" - {e}" for e in errors)
        logger.critical(error_msg)
        raise RuntimeError(error_msg)

    logger.info("✅ Corpus manifest and embedder configuration verified successfully.")
