"""Knowledge Base Build Job (P3.10).

Builds full partitioned/versioned KB chunks and dense embeddings into PostgreSQL pgvector,
staging the version for zero-downtime promotion via kb_promote.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from app.adapters.local.embedder import LocalEmbedder
from app.adapters.postgres.vector_index import PostgresVectorIndex
from app.core.config import get_settings
from pipeline.loaders.policy_loader import load_policy_markdown_files
from pipeline.manifest import CorpusManifestManager
from pipeline.normalizers.policy_normalizer import PolicyNormalizer
from pipeline.processors.chunking import HeadingAwareMarkdownChunker

repo_root = Path(__file__).resolve().parent.parent.parent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


async def build_kb(
    target_version: str = "v1",
    store_filter: str = "all",
    batch_size: int = 50,
    status: str = "active",
) -> dict[str, int]:
    """Execute knowledge base indexing build."""
    settings = get_settings()
    manifest_mgr = CorpusManifestManager(repo_root=repo_root)
    embedder = LocalEmbedder(model_name=settings.EMBEDDER_MODEL, dim=settings.EMBEDDING_DIM)
    vector_index = PostgresVectorIndex(active_version=target_version)

    stats = {"policy_chunks": 0, "faq_chunks": 0}

    # 1. Build Policy Store
    if store_filter in ("all", "policy"):
        logger.info(f"Building Policy Corpus (version={target_version})...")
        policy_loader = load_policy_markdown_files(repo_root / "corpora" / "policy")
        normalizer = PolicyNormalizer()
        chunker = HeadingAwareMarkdownChunker()

        chunks_to_index: list[dict[str, Any]] = []

        for raw in policy_loader:
            norm = normalizer.normalize(raw)
            if not norm:
                continue
            policy_chunks = chunker.chunk_record(norm)
            for c in policy_chunks:
                chunks_to_index.append(
                    {
                        "chunk_id": c.chunk_id,
                        "store_type": "policy",
                        "title": c.title,
                        "text": c.text,
                        "intent_label": c.intent_labels[0] if c.intent_labels else None,
                        "token_count": c.token_count,
                        "metadata": {
                            **c.metadata,
                            "status": status,
                            "version_tag": target_version,
                        },
                    }
                )

        logger.info(f"Embedding and upserting {len(chunks_to_index)} policy chunks...")
        for i in range(0, len(chunks_to_index), batch_size):
            batch = chunks_to_index[i : i + batch_size]
            texts = [b["text"] for b in batch]
            ids = [b["chunk_id"] for b in batch]
            metas = [b["metadata"] for b in batch]

            vectors = await embedder.embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")
            await vector_index.upsert("policy", ids, vectors, metas)

        stats["policy_chunks"] = len(chunks_to_index)
        logger.info(f"Indexed {stats['policy_chunks']} policy chunks.")

    # 2. Build FAQ Store
    if store_filter in ("all", "faq"):
        logger.info(f"Building FAQ Corpus (version={target_version})...")
        faq_norm_file = (
            repo_root / "data" / "processed" / "normalized" / "faq" / "faq.normalized.jsonl"
        )

        faq_records: list[dict[str, Any]] = []
        if faq_norm_file.exists():
            with open(faq_norm_file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        faq_records.append(json.loads(line))

        # Build chunks
        faq_chunks_to_index: list[dict[str, Any]] = []
        for rec in faq_records:
            chunk_id = f"faq_{rec['id']}"
            title = rec.get("title", "FAQ")
            text = rec.get("text", "")
            intent = rec.get("metadata", {}).get("intent_label")
            meta = {
                "chunk_id": chunk_id,
                "store_type": "faq",
                "title": title,
                "text": text,
                "intent_label": intent,
                "status": status,
                "version_tag": target_version,
                **rec.get("metadata", {}),
            }
            faq_chunks_to_index.append(
                {
                    "chunk_id": chunk_id,
                    "title": title,
                    "text": text,
                    "meta": meta,
                }
            )

        logger.info(f"Embedding and upserting {len(faq_chunks_to_index)} FAQ chunks...")
        for i in range(0, len(faq_chunks_to_index), batch_size):
            batch = faq_chunks_to_index[i : i + batch_size]
            texts = [b["text"] for b in batch]
            ids = [b["chunk_id"] for b in batch]
            metas = [b["meta"] for b in batch]

            vectors = await embedder.embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")
            await vector_index.upsert("faq", ids, vectors, metas)

        stats["faq_chunks"] = len(faq_chunks_to_index)
        logger.info(f"Indexed {stats['faq_chunks']} FAQ chunks.")

    # 3. Update manifest
    manifest_mgr.write_manifest(
        corpus_version=target_version,
        embedder_model=settings.EMBEDDER_MODEL,
        embedding_dim=settings.EMBEDDING_DIM,
    )
    logger.info(f"✅ KB build complete for version {target_version}: {stats}")
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Knowledge Base Build Job")
    parser.add_argument("--version", default="v1", help="Target corpus version tag")
    parser.add_argument(
        "--store", default="all", choices=["all", "policy", "faq"], help="Store to index"
    )
    parser.add_argument(
        "--status", default="active", choices=["active", "staging"], help="Initial chunk status"
    )
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for embedding")
    args = parser.parse_args()

    asyncio.run(
        build_kb(
            target_version=args.version,
            store_filter=args.store,
            batch_size=args.batch_size,
            status=args.status,
        )
    )


if __name__ == "__main__":
    main()
