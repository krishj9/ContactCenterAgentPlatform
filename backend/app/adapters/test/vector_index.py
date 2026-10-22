"""Test adapter for VectorIndex port."""

from __future__ import annotations

import math
from typing import Any


class TestVectorIndex:
    """In-memory vector index with cosine similarity search."""

    __test__ = False

    def __init__(self) -> None:
        # store_type -> {id: (vector, metadata)}
        self._stores: dict[str, dict[str, tuple[list[float], dict[str, Any]]]] = {}

    def _cosine(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    async def search(
        self,
        store_type: str,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[tuple[str, float]]:
        store = self._stores.get(store_type, {})
        scored: list[tuple[str, float]] = []

        for chunk_id, (vec, meta) in store.items():
            if filters:
                matches = all(meta.get(k) == v for k, v in filters.items())
                if not matches:
                    continue
            sim = self._cosine(query_vector, vec)
            scored.append((chunk_id, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    async def upsert(
        self,
        store_type: str,
        ids: list[str],
        vectors: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        if store_type not in self._stores:
            self._stores[store_type] = {}

        for rec_id, vec, meta in zip(ids, vectors, metadatas, strict=False):
            self._stores[store_type][rec_id] = (vec, meta)
