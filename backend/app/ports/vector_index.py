"""Port protocol for vector indexing and hybrid retrieval."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class VectorIndex(Protocol):
    """Protocol for vector indexing backends (HNSW dense + full-text sparse)."""

    async def search(
        self,
        store_type: str,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[tuple[str, float]]:
        """Search vector store and return list of (chunk_id, similarity_score)."""
        ...

    async def upsert(
        self,
        store_type: str,
        ids: list[str],
        vectors: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Upsert records with embeddings and metadata."""
        ...
