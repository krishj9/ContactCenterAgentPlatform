"""Port protocol for cross-encoder reranking."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.evidence import EvidenceChunk


@runtime_checkable
class Reranker(Protocol):
    """Protocol for cross-encoder reranking of retrieved evidence candidates."""

    async def rerank(
        self,
        query: str,
        candidates: list[EvidenceChunk],
        top_k: int = 5,
    ) -> list[EvidenceChunk]:
        """Rerank candidates against the query and return the top_k."""
        ...
