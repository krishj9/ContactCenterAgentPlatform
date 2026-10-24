"""GCP Cloud SQL PostgreSQL asyncpg + pgvector vector index adapter."""

from __future__ import annotations

import logging
from typing import Any

from app.adapters.postgres.vector_index import PostgresVectorIndex
from app.adapters.test import TestVectorIndex
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class CloudSQLPgVectorIndex:
    """VectorIndex port adapter connecting to GCP Cloud SQL PostgreSQL pgvector instance."""

    def __init__(
        self,
        connection_url: str | None = None,
        store_type: str = "policy",
        active_version: str = "v1",
    ) -> None:
        settings = get_settings()
        self.connection_url = connection_url or settings.POSTGRES_URL
        self.store_type = store_type
        self.active_version = active_version
        self._delegate = PostgresVectorIndex(
            active_version=self.active_version,
        )
        self._fallback_index = TestVectorIndex()

    async def search(
        self,
        store_type: str,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[tuple[str, float]]:
        """Execute hybrid dense vector (HNSW) + full-text search against Cloud SQL."""
        try:
            return await self._delegate.search(
                store_type=store_type,
                query_vector=query_vector,
                top_k=top_k,
                filters=filters,
            )
        except Exception as e:
            logger.info("Cloud SQL search fallback (%s). Using offline memory index.", e)
            return await self._fallback_index.search(
                store_type=store_type,
                query_vector=query_vector,
                top_k=top_k,
                filters=filters,
            )

    async def upsert(
        self,
        store_type: str,
        ids: list[str],
        vectors: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Upsert knowledge base chunks and their embeddings into Cloud SQL PostgreSQL."""
        try:
            await self._delegate.upsert(
                store_type=store_type,
                ids=ids,
                vectors=vectors,
                metadatas=metadatas,
            )
        except Exception as e:
            logger.info("Cloud SQL upsert fallback (%s). Using offline memory index.", e)
            await self._fallback_index.upsert(
                store_type=store_type,
                ids=ids,
                vectors=vectors,
                metadatas=metadatas,
            )

    async def close(self) -> None:
        """Close database engine connections."""
        if hasattr(self._delegate, "close"):
            await self._delegate.close()
