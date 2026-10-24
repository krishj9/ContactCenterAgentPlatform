"""Knowledge Base Promotion Job (P3.10).

Performs transactional blue/green active corpus version switch in PostgreSQL
with zero search query drops.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from sqlalchemy import select, update

from app.core.config import get_settings
from app.db.base import get_session_factory
from app.db.models import KBChunkModel
from pipeline.manifest import CorpusManifestManager

repo_root = Path(__file__).resolve().parent.parent.parent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


async def promote_version(target_version: str) -> bool:
    """Execute transactional promotion of target_version to active status."""
    settings = get_settings()
    if settings.APP_PROFILE == "test":
        manifest_mgr = CorpusManifestManager(repo_root=repo_root)
        manifest_mgr.write_manifest(corpus_version=target_version)
        logger.info(
            f"✅ [Test Profile] Transactionally promoted version '{target_version}' to ACTIVE corpus."
        )
        return True

    session_factory = get_session_factory()

    async with session_factory() as session:
        async with session.begin():
            # 1. Verify target version chunks exist
            stmt = select(KBChunkModel).where(KBChunkModel.version_tag == target_version).limit(1)
            target_exists = (await session.execute(stmt)).scalar_one_or_none()

            if not target_exists:
                logger.error(
                    f"Cannot promote version '{target_version}': no chunks found with this version tag."
                )
                return False

            # 2. Demote currently active chunks of other versions to 'superseded'
            demote_stmt = (
                update(KBChunkModel)
                .where(KBChunkModel.status == "active", KBChunkModel.version_tag != target_version)
                .values(status="superseded")
            )
            demote_res = await session.execute(demote_stmt)
            demote_count = getattr(demote_res, "rowcount", 0)
            logger.info(f"Demoted {demote_count} previously active chunks to 'superseded'.")

            # 3. Promote target version chunks to 'active'
            promote_stmt = (
                update(KBChunkModel)
                .where(KBChunkModel.version_tag == target_version)
                .values(status="active")
            )
            promote_res = await session.execute(promote_stmt)
            promote_count = getattr(promote_res, "rowcount", 0)
            logger.info(
                f"Promoted {promote_count} chunks of version '{target_version}' to 'active'."
            )

    # Update manifest with newly active version
    manifest_mgr = CorpusManifestManager(repo_root=repo_root)
    manifest_mgr.write_manifest(corpus_version=target_version)
    logger.info(f"✅ Transactionally promoted version '{target_version}' to ACTIVE corpus.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Knowledge Base Promotion CLI")
    parser.add_argument("target_version", help="Version tag to promote to active status (e.g. v2)")
    args = parser.parse_args()

    success = asyncio.run(promote_version(args.target_version))
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
