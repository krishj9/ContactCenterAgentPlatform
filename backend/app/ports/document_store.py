"""Port protocol for relational and document storage."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DocumentStore(Protocol):
    """Protocol for document store hydration and metadata access."""

    async def get_by_id(self, doc_id: str) -> dict[str, Any] | None:
        """Fetch a single document by its ID."""
        ...

    async def get_many(self, doc_ids: list[str]) -> list[dict[str, Any]]:
        """Fetch multiple documents in a single batch query."""
        ...

    async def upsert(self, doc_id: str, data: dict[str, Any]) -> None:
        """Upsert a document record."""
        ...
