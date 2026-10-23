"""PostgreSQL pgvector VectorIndex Adapter (P3.9).

Implements the VectorIndex port protocol supporting:
- Dense HNSW cosine similarity search (<=> operator)
- Sparse tsvector full-text search with plainto_tsquery
- Reciprocal Rank Fusion (RRF: w_dense=0.6, w_sparse=0.4, k=60)
- Metadata filtering on intent_labels, is_active/status
- Active version routing for zero-downtime blue/green deployments
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.base import get_session_factory
from app.db.models import KBChunkModel
from app.ports.vector_index import VectorIndex

logger = logging.getLogger(__name__)

RRF_K = 60
WEIGHT_DENSE = 0.6
WEIGHT_SPARSE = 0.4


class PostgresVectorIndex(VectorIndex):
    """PostgreSQL pgvector repository with hybrid dense + sparse RRF search."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        active_version: str = "v1",
    ) -> None:
        self.session_factory = session_factory or get_session_factory()
        self.active_version = active_version

    async def search(
        self,
        store_type: str,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[tuple[str, float]]:
        """Hybrid vector search combining dense cosine and sparse tsvector via RRF."""
        filters = filters or {}
        query_text = filters.get("query_text")
        intent_filter = filters.get("intent_label") or filters.get("intent")
        status_filter = filters.get("status", "active")
        if "is_active" in filters:
            status_filter = "active" if filters["is_active"] else "retired"

        version_filter = filters.get("version_tag", self.active_version)

        async with self.session_factory() as session:
            # 1. Dense retrieval (HNSW cosine distance)
            distance_expr = KBChunkModel.embedding.op("<=>")(query_vector)

            dense_stmt = select(
                KBChunkModel.chunk_id,
                (1.0 - distance_expr).label("similarity_score"),
            ).where(
                KBChunkModel.store_type == store_type,
                KBChunkModel.embedding.is_not(None),
            )

            if status_filter:
                dense_stmt = dense_stmt.where(KBChunkModel.status == status_filter)
            if version_filter and version_filter != "*":
                dense_stmt = dense_stmt.where(KBChunkModel.version_tag == version_filter)
            if intent_filter:
                # Match either column intent_label or within metadata_json
                dense_stmt = dense_stmt.where(
                    (KBChunkModel.intent_label == intent_filter)
                    | (
                        func.json_extract_path_text(
                            KBChunkModel.metadata_json, "intent_labels"
                        ).like(f"%{intent_filter}%")
                    )
                )

            dense_candidates_k = max(top_k * 3, 30)
            dense_stmt = dense_stmt.order_by(distance_expr.asc()).limit(dense_candidates_k)
            dense_result = await session.execute(dense_stmt)
            dense_rows = dense_result.all()

            # If no query_text is given for sparse search, return pure dense search results
            if not query_text:
                return [(row[0], float(row[1])) for row in dense_rows[:top_k]]

            # 2. Sparse full-text retrieval (tsvector @@ plainto_tsquery)
            clean_query = query_text.replace("'", " ").replace('"', " ").strip()
            if not clean_query:
                return [(row[0], float(row[1])) for row in dense_rows[:top_k]]

            ts_query_expr = func.plainto_tsquery("english", clean_query)
            ts_rank_expr = func.ts_rank(KBChunkModel.tsv, ts_query_expr)

            sparse_stmt = select(
                KBChunkModel.chunk_id,
                ts_rank_expr.label("rank_score"),
            ).where(
                KBChunkModel.store_type == store_type,
                KBChunkModel.tsv.op("@@")(ts_query_expr),
            )

            if status_filter:
                sparse_stmt = sparse_stmt.where(KBChunkModel.status == status_filter)
            if version_filter and version_filter != "*":
                sparse_stmt = sparse_stmt.where(KBChunkModel.version_tag == version_filter)
            if intent_filter:
                sparse_stmt = sparse_stmt.where(
                    (KBChunkModel.intent_label == intent_filter)
                    | (
                        func.json_extract_path_text(
                            KBChunkModel.metadata_json, "intent_labels"
                        ).like(f"%{intent_filter}%")
                    )
                )

            sparse_stmt = sparse_stmt.order_by(ts_rank_expr.desc()).limit(dense_candidates_k)
            sparse_result = await session.execute(sparse_stmt)
            sparse_rows = sparse_result.all()

            # 3. Reciprocal Rank Fusion (RRF)
            # RRF(d) = sum_m (w_m / (k + rank_m(d)))
            dense_ranks = {row[0]: rank for rank, row in enumerate(dense_rows, start=1)}
            sparse_ranks = {row[0]: rank for rank, row in enumerate(sparse_rows, start=1)}

            all_candidates = set(dense_ranks.keys()).union(sparse_ranks.keys())
            rrf_scores: dict[str, float] = {}

            for doc_id in all_candidates:
                score = 0.0
                if doc_id in dense_ranks:
                    score += WEIGHT_DENSE / (RRF_K + dense_ranks[doc_id])
                if doc_id in sparse_ranks:
                    score += WEIGHT_SPARSE / (RRF_K + sparse_ranks[doc_id])
                rrf_scores[doc_id] = score

            ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
            return ranked[:top_k]

    async def upsert(
        self,
        store_type: str,
        ids: list[str],
        vectors: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Upsert batch of chunks computing both pgvector embedding and tsvector."""
        async with self.session_factory() as session:
            for chunk_id, vector, meta in zip(ids, vectors, metadatas, strict=False):
                stmt = select(KBChunkModel).where(KBChunkModel.chunk_id == chunk_id)
                existing = (await session.execute(stmt)).scalar_one_or_none()

                title = meta.get("title", meta.get("question", f"Chunk {chunk_id}"))
                text_content = meta.get("text", meta.get("answer", ""))
                intent_label = meta.get("intent_label", meta.get("intent"))
                if not intent_label and meta.get("intent_labels"):
                    intent_label = meta["intent_labels"][0]

                token_count = meta.get("token_count", len(text_content.split()))
                status = meta.get("status", "active")
                version_tag = meta.get("version_tag", self.active_version)

                # tsvector expression for full-text indexing
                tsv_expr = func.to_tsvector("english", f"{title} {text_content}")

                if existing:
                    existing.store_type = store_type
                    existing.title = title
                    existing.text = text_content
                    existing.intent_label = intent_label
                    existing.token_count = token_count
                    existing.embedding = vector
                    existing.tsv = tsv_expr
                    existing.status = status
                    existing.version_tag = version_tag
                    existing.metadata_json = meta
                else:
                    new_chunk = KBChunkModel(
                        chunk_id=chunk_id,
                        store_type=store_type,
                        title=title,
                        text=text_content,
                        intent_label=intent_label,
                        token_count=token_count,
                        embedding=vector,
                        tsv=tsv_expr,
                        status=status,
                        version_tag=version_tag,
                        metadata_json=meta,
                    )
                    session.add(new_chunk)

            await session.commit()
