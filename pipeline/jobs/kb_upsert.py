"""Knowledge Base Incremental Upsert and Retirement Job (P3.10).

Enables granular updates, incremental document re-indexing, or immediate chunk retirement
without requiring a full corpus rebuild.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from sqlalchemy import update

from app.adapters.local.embedder import LocalEmbedder
from app.adapters.postgres.vector_index import PostgresVectorIndex
from app.core.config import get_settings
from app.db.base import get_session_factory
from app.db.models import KBChunkModel
from pipeline.loaders.policy_loader import load_policy_markdown_files
from pipeline.normalizers.policy_normalizer import PolicyNormalizer
from pipeline.processors.chunking import HeadingAwareMarkdownChunker

repo_root = Path(__file__).resolve().parent.parent.parent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


async def upsert_policy_file(file_path: Path, active_version: str = "v1") -> int:
    """Incrementally parse, chunk, embed, and upsert a single policy Markdown file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Policy file not found: {file_path}")

    settings = get_settings()
    embedder = LocalEmbedder(model_name=settings.EMBEDDER_MODEL, dim=settings.EMBEDDING_DIM)
    vector_index = PostgresVectorIndex(active_version=active_version)

    records = list(load_policy_markdown_files(file_path.parent))
    target_record = next((r for r in records if Path(r["file_path"]).name == file_path.name), None)

    if not target_record:
        raise ValueError(f"Could not load valid policy record from {file_path}")

    normalizer = PolicyNormalizer()
    chunker = HeadingAwareMarkdownChunker()

    norm = normalizer.normalize(target_record)
    if not norm:
        raise ValueError(f"Failed to normalize {file_path}")

    chunks = chunker.chunk_record(norm)
    texts = [c.text for c in chunks]
    ids = [c.chunk_id for c in chunks]
    metas = [{**c.metadata, "status": "active", "version_tag": active_version} for c in chunks]

    vectors = await embedder.embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")
    await vector_index.upsert("policy", ids, vectors, metas)

    logger.info(f"✅ Incrementally upserted {len(chunks)} chunks for {file_path.name}")
    return len(chunks)


async def retire_chunk_or_policy(identifier: str) -> int:
    """Mark chunk(s) matching chunk_id or policy_id prefix as 'retired'."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        async with session.begin():
            stmt = (
                update(KBChunkModel)
                .where(
                    (KBChunkModel.chunk_id == identifier)
                    | (KBChunkModel.chunk_id.like(f"%{identifier.lower().replace('-', '_')}%"))
                )
                .values(status="retired")
            )
            res = await session.execute(stmt)
            count = int(getattr(res, "rowcount", 0))
            logger.info(f"✅ Retired {count} chunk(s) matching '{identifier}'.")
            return count


def main() -> None:
    parser = argparse.ArgumentParser(description="KB Incremental Upsert and Retire CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    upsert_parser = subparsers.add_parser("upsert", help="Upsert a policy Markdown file")
    upsert_parser.add_argument("file_path", help="Path to policy Markdown file")
    upsert_parser.add_argument("--version", default="v1", help="Version tag")

    retire_parser = subparsers.add_parser("retire", help="Retire a chunk or policy")
    retire_parser.add_argument("identifier", help="Chunk ID or Policy ID to retire")

    args = parser.parse_args()

    if args.command == "upsert":
        asyncio.run(upsert_policy_file(Path(args.file_path), active_version=args.version))
    elif args.command == "retire":
        asyncio.run(retire_chunk_or_policy(args.identifier))


if __name__ == "__main__":
    main()
