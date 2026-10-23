"""PostgreSQL pgvector repositories implementing VectorIndex and DocumentStore ports."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.base import get_session_factory
from app.db.models import KBChunkModel
from app.ports.document_store import DocumentStore
from app.ports.vector_index import VectorIndex


class PostgresKBChunkRepository(VectorIndex):
    """PostgreSQL pgvector repository implementing VectorIndex port protocol."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None) -> None:
        self.session_factory = session_factory or get_session_factory()

    async def search(
        self,
        store_type: str,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[tuple[str, float]]:
        """Vector similarity search using pgvector cosine distance (<=>)."""
        async with self.session_factory() as session:
            # Cosine distance: 0 = identical, 1 = orthogonal, 2 = opposite
            distance_expr = KBChunkModel.embedding.op("<=>")(query_vector)

            stmt = select(
                KBChunkModel.chunk_id,
                (1.0 - distance_expr).label("similarity_score"),
            ).where(
                KBChunkModel.store_type == store_type,
                KBChunkModel.status == "active",
                KBChunkModel.embedding.is_not(None),
            )

            # Apply metadata filters if provided
            if filters:
                if "intent_label" in filters:
                    stmt = stmt.where(KBChunkModel.intent_label == filters["intent_label"])
                if "status" in filters:
                    stmt = stmt.where(KBChunkModel.status == filters["status"])

            stmt = stmt.order_by(distance_expr.asc()).limit(top_k)
            result = await session.execute(stmt)
            rows = result.all()

            return [(row[0], float(row[1])) for row in rows]

    async def upsert(
        self,
        store_type: str,
        ids: list[str],
        vectors: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Upsert batch of chunks with embeddings and metadata."""
        async with self.session_factory() as session:
            for chunk_id, vector, meta in zip(ids, vectors, metadatas, strict=False):
                stmt = select(KBChunkModel).where(KBChunkModel.chunk_id == chunk_id)
                existing = (await session.execute(stmt)).scalar_one_or_none()

                title = meta.get("title", meta.get("question", f"Chunk {chunk_id}"))
                text = meta.get("text", meta.get("answer", ""))
                intent_label = meta.get("intent_label", meta.get("intent"))
                status = meta.get("status", "active")
                version_tag = meta.get("version_tag", "v1")

                if existing:
                    existing.store_type = store_type
                    existing.title = title
                    existing.text = text
                    existing.intent_label = intent_label
                    existing.embedding = vector
                    existing.status = status
                    existing.version_tag = version_tag
                    existing.metadata_json = meta
                else:
                    new_chunk = KBChunkModel(
                        chunk_id=chunk_id,
                        store_type=store_type,
                        title=title,
                        text=text,
                        intent_label=intent_label,
                        embedding=vector,
                        status=status,
                        version_tag=version_tag,
                        metadata_json=meta,
                    )
                    session.add(new_chunk)

            await session.commit()


class PostgresDocumentStoreRepository(DocumentStore):
    """PostgreSQL document repository implementing DocumentStore port protocol."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None) -> None:
        self.session_factory = session_factory or get_session_factory()

    async def get_by_id(self, doc_id: str) -> dict[str, Any] | None:
        """Fetch single document chunk by ID."""
        async with self.session_factory() as session:
            stmt = select(KBChunkModel).where(KBChunkModel.chunk_id == doc_id)
            chunk = (await session.execute(stmt)).scalar_one_or_none()
            if not chunk:
                return None
            return {
                "chunk_id": chunk.chunk_id,
                "store_type": chunk.store_type,
                "title": chunk.title,
                "text": chunk.text,
                "intent_label": chunk.intent_label,
                "status": chunk.status,
                "metadata": chunk.metadata_json or {},
            }

    async def get_many(self, doc_ids: list[str]) -> list[dict[str, Any]]:
        """Fetch multiple document chunks by IDs."""
        if not doc_ids:
            return []
        async with self.session_factory() as session:
            stmt = select(KBChunkModel).where(KBChunkModel.chunk_id.in_(doc_ids))
            chunks = (await session.execute(stmt)).scalars().all()
            return [
                {
                    "chunk_id": chunk.chunk_id,
                    "store_type": chunk.store_type,
                    "title": chunk.title,
                    "text": chunk.text,
                    "intent_label": chunk.intent_label,
                    "status": chunk.status,
                    "metadata": chunk.metadata_json or {},
                }
                for chunk in chunks
            ]

    async def upsert(self, doc_id: str, data: dict[str, Any]) -> None:
        """Upsert a document record into the document store."""
        async with self.session_factory() as session:
            stmt = select(KBChunkModel).where(KBChunkModel.chunk_id == doc_id)
            existing = (await session.execute(stmt)).scalar_one_or_none()

            store_type = data.get("store_type", "policy")
            title = data.get("title", f"Doc {doc_id}")
            text = data.get("text", "")
            intent_label = data.get("intent_label")
            status = data.get("status", "active")
            version_tag = data.get("version_tag", "v1")

            if existing:
                existing.store_type = store_type
                existing.title = title
                existing.text = text
                existing.intent_label = intent_label
                existing.status = status
                existing.version_tag = version_tag
                existing.metadata_json = data
            else:
                new_chunk = KBChunkModel(
                    chunk_id=doc_id,
                    store_type=store_type,
                    title=title,
                    text=text,
                    intent_label=intent_label,
                    status=status,
                    version_tag=version_tag,
                    metadata_json=data,
                )
                session.add(new_chunk)

            await session.commit()
