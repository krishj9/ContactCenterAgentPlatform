"""Test adapter for Embedder port."""

from __future__ import annotations

import hashlib
import math


class TestEmbedder:
    """Deterministic hash-based dense embedder for testing."""

    __test__ = False

    def __init__(self, dim: int = 768) -> None:
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    def _hash_to_vector(self, text: str) -> list[float]:
        """Generate deterministic normalized unit vector from SHA256 seed."""
        vec = []
        seed = text.encode("utf-8")
        norm_sq = 0.0
        for i in range(self._dim):
            h = hashlib.sha256(seed + i.to_bytes(4, "big")).digest()
            val = (int.from_bytes(h[:4], "big") / 2**32) * 2.0 - 1.0
            vec.append(val)
            norm_sq += val * val

        norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
        return [v / norm for v in vec]

    async def embed_texts(
        self,
        texts: list[str],
        task_type: str = "RETRIEVAL_DOCUMENT",
    ) -> list[list[float]]:
        return [self._hash_to_vector(t) for t in texts]

    async def embed_query(self, query: str) -> list[float]:
        return self._hash_to_vector(query)
