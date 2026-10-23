"""Unit tests for LocalEmbedder (P3.8)."""

from __future__ import annotations

import pytest

from app.adapters.local.embedder import LocalEmbedder
from app.ports.embedder import Embedder


@pytest.mark.asyncio
async def test_embedder_conforms_to_port() -> None:
    embedder = LocalEmbedder(force_offline=True)
    assert isinstance(embedder, Embedder)
    assert embedder.dim == 768


@pytest.mark.asyncio
async def test_embed_texts_and_query() -> None:
    embedder = LocalEmbedder(force_offline=True)

    # Document embedding
    docs = [
        "Card decline resolution procedure for retail banking.",
        "Foreign transaction travel exemption guidelines.",
    ]
    doc_vectors = await embedder.embed_texts(docs, task_type="RETRIEVAL_DOCUMENT")
    assert len(doc_vectors) == 2
    assert len(doc_vectors[0]) == 768
    assert len(doc_vectors[1]) == 768

    # Query embedding
    q_vec = await embedder.embed_query("Why was my credit card declined?")
    assert len(q_vec) == 768

    # Check normalization: L2 norm should be approx 1.0
    norm_sq = sum(x * x for x in q_vec)
    assert 0.99 <= norm_sq <= 1.01
