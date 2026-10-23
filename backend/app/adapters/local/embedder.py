"""Local Embedder Adapter (P3.8).

Implements the Embedder port protocol for dense 768-dimensional vector representations.
Uses SentenceTransformer when available, with a deterministic offline hashing projection
fallback for offline test isolation (R10, R13, pytest-socket).
"""

from __future__ import annotations

import hashlib
import logging
import math
from typing import Any

from app.ports.embedder import Embedder

logger = logging.getLogger(__name__)


def _deterministic_mock_vector(text: str, dim: int = 768) -> list[float]:
    """Generate deterministic, L2-normalized pseudo-embedding vector for offline tests.

    Tokens in text are hashed to buckets with sign hashing to produce meaningful
    cosine similarity based on term overlap without external weights.
    """
    vec = [0.0] * dim
    words = text.lower().strip().split()
    if not words:
        words = ["empty"]

    for word in words:
        h = hashlib.sha256(word.encode("utf-8")).digest()
        idx = int.from_bytes(h[:4], "big") % dim
        sign = 1.0 if (h[4] % 2 == 0) else -1.0
        vec[idx] += sign

    # Add character n-grams for subword similarity
    for i in range(len(text) - 2):
        trigram = text[i : i + 3].lower()
        h = hashlib.md5(trigram.encode("utf-8")).digest()
        idx = int.from_bytes(h[:4], "big") % dim
        sign = 0.5 if (h[4] % 2 == 0) else -0.5
        vec[idx] += sign

    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        norm = 1.0
    return [v / norm for v in vec]


class LocalEmbedder(Embedder):
    """Local embedding adapter supporting query/document task-type prefixes and 768d output."""

    def __init__(
        self,
        model_name: str = "EmbeddingGemma",
        dim: int = 768,
        query_prefix: str = "task: search query | query: ",
        doc_prefix: str = "task: search document | document: ",
        force_offline: bool = False,
    ) -> None:
        self._model_name = model_name
        self._dim = dim
        self._query_prefix = query_prefix
        self._doc_prefix = doc_prefix
        self._force_offline = force_offline
        self._model: Any = None

        if not force_offline:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(model_name)
                logger.info("Loaded SentenceTransformer model: %s", model_name)
            except Exception as e:
                logger.info(
                    "SentenceTransformer not loaded (%s). Using deterministic offline embedder.",
                    str(e),
                )
                self._model = None

    @property
    def dim(self) -> int:
        return self._dim

    async def embed_texts(
        self,
        texts: list[str],
        task_type: str = "RETRIEVAL_DOCUMENT",
    ) -> list[list[float]]:
        """Embed a batch of document or passage texts."""
        prefix = self._doc_prefix if task_type == "RETRIEVAL_DOCUMENT" else self._query_prefix
        prefixed = [f"{prefix}{t}" for t in texts]

        if self._model is not None:
            embeddings = self._model.encode(prefixed, convert_to_numpy=True)
            return [e.tolist() for e in embeddings]

        return [_deterministic_mock_vector(t, self._dim) for t in prefixed]

    async def embed_query(self, query: str) -> list[float]:
        """Embed a single search query with query prefix."""
        results = await self.embed_texts([query], task_type="RETRIEVAL_QUERY")
        return results[0]
