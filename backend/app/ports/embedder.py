"""Port protocol for vector embedding models."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Embedder(Protocol):
    """Protocol for dense vector embedding models."""

    @property
    def dim(self) -> int:
        """Vector dimensionality (e.g., 768)."""
        ...

    async def embed_texts(
        self,
        texts: list[str],
        task_type: str = "RETRIEVAL_DOCUMENT",
    ) -> list[list[float]]:
        """Embed a batch of document texts."""
        ...

    async def embed_query(self, query: str) -> list[float]:
        """Embed a single search query."""
        ...
