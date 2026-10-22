"""Test adapter for DocumentStore port."""

from __future__ import annotations

from typing import Any


class TestDocumentStore:
    """In-memory dictionary document store."""

    __test__ = False

    def __init__(self, seed_data: dict[str, dict[str, Any]] | None = None) -> None:
        self._data: dict[str, dict[str, Any]] = seed_data.copy() if seed_data else {}

    async def get_by_id(self, doc_id: str) -> dict[str, Any] | None:
        return self._data.get(doc_id)

    async def get_many(self, doc_ids: list[str]) -> list[dict[str, Any]]:
        return [self._data[doc_id] for doc_id in doc_ids if doc_id in self._data]

    async def upsert(self, doc_id: str, data: dict[str, Any]) -> None:
        self._data[doc_id] = data
