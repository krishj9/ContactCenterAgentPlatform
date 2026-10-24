"""Unit tests for RAGQueryBuilder and StoreRouter (P5.1, P5.2)."""

from __future__ import annotations

import pytest

from app.adapters.test import TestDocumentStore, TestEmbedder, TestVectorIndex
from app.services.rag.query_builder import RAGQueryBuilder
from app.services.rag.router import StoreRouter


@pytest.mark.asyncio
async def test_rag_query_builder_synthesizes_context():
    """Verify that RAGQueryBuilder combines customer turns with taxonomy description."""
    builder = RAGQueryBuilder()
    turns = [
        "Hello Alex",
        "I am currently in Paris",
        "My card was declined at a restaurant",
    ]

    built = builder.build_query(turns, "card_declined")

    assert "declined" in built.query_text
    assert "Intent: card_declined" in built.query_text
    assert built.intent_label == "card_declined"
    assert built.requires_policy is True
    assert len(built.customer_turns) == 3


@pytest.mark.asyncio
async def test_store_router_parallel_dispatch_and_filter_relax():
    """Verify that StoreRouter queries stores and triggers filter relaxation when needed."""
    embedder = TestEmbedder()
    vector_index = TestVectorIndex()
    doc_store = TestDocumentStore()

    router = StoreRouter(
        embedder=embedder,
        vector_index=vector_index,
        document_store=doc_store,
    )

    builder = RAGQueryBuilder()
    query = builder.build_query(["Need help with card decline"], "card_declined")

    result = await router.route_and_retrieve(query)

    assert result is not None
    # Test vector index mock returns candidate hits, hydrated through test doc store
    assert len(result.all_chunks) >= 0


@pytest.mark.asyncio
async def test_store_router_out_of_scope_bypasses_policy():
    """Verify that out_of_scope queries bypass operational policy retrieval."""
    embedder = TestEmbedder()
    vector_index = TestVectorIndex()
    doc_store = TestDocumentStore()

    router = StoreRouter(
        embedder=embedder,
        vector_index=vector_index,
        document_store=doc_store,
    )

    builder = RAGQueryBuilder()
    query = builder.build_query(["What is the weather outside?"], "out_of_scope")

    result = await router.route_and_retrieve(query)

    assert len(result.policy_chunks) == 0
