"""Unit tests verifying all Port protocols, test adapters, and DI container."""

import pytest

from app.adapters.test import (
    TestBlobStore,
    TestDocumentStore,
    TestEmbedder,
    TestEventBus,
    TestGenerator,
    TestIntentClassifier,
    TestPIIRedactor,
    TestReranker,
    TestSessionStateStore,
    TestSpeechToText,
    TestVectorIndex,
)
from app.core.config import Settings
from app.core.container import Container
from app.ports import (
    BlobStore,
    DocumentStore,
    Embedder,
    EventBus,
    Generator,
    IntentClassifier,
    PIIRedactor,
    Reranker,
    SessionStateStore,
    SpeechToText,
    VectorIndex,
)


def test_adapters_satisfy_protocols():
    """Verify that every test adapter satisfies its runtime-checkable Protocol."""
    assert isinstance(TestIntentClassifier(), IntentClassifier)
    assert isinstance(TestSpeechToText(), SpeechToText)
    assert isinstance(TestEmbedder(), Embedder)
    assert isinstance(TestVectorIndex(), VectorIndex)
    assert isinstance(TestDocumentStore(), DocumentStore)
    assert isinstance(TestReranker(), Reranker)
    assert isinstance(TestGenerator(), Generator)
    assert isinstance(TestSessionStateStore(), SessionStateStore)
    assert isinstance(TestEventBus(), EventBus)
    assert isinstance(TestBlobStore(), BlobStore)
    assert isinstance(TestPIIRedactor(), PIIRedactor)


@pytest.mark.asyncio
async def test_container_dependency_injection():
    """Test DI container initialization and adapter resolution."""
    settings = Settings(APP_PROFILE="test")
    container = Container(settings)

    assert isinstance(container.intent_classifier, IntentClassifier)
    assert isinstance(container.generator, Generator)

    # Test override mechanism
    custom_classifier = TestIntentClassifier(default_intent="travel_notice")
    container.override("intent_classifier", custom_classifier)
    pred = await container.intent_classifier.classify(["I need help"])
    assert pred.intent_label == "travel_notice"

    container.reset_overrides()
    pred_reset = await container.intent_classifier.classify(["I need help"])
    assert pred_reset.intent_label == "card_declined"


@pytest.mark.asyncio
async def test_embedder_and_vector_index():
    embedder = TestEmbedder(dim=768)
    assert embedder.dim == 768

    vectors = await embedder.embed_texts(["hello world", "banking policy"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 768

    query_vec = await embedder.embed_query("banking policy")
    assert len(query_vec) == 768

    index = TestVectorIndex()
    await index.upsert(
        store_type="policy",
        ids=["chunk-01", "chunk-02"],
        vectors=vectors,
        metadatas=[{"title": "doc1"}, {"title": "doc2"}],
    )

    results = await index.search(store_type="policy", query_vector=query_vec, top_k=2)
    assert len(results) == 2
    assert results[0][0] == "chunk-02"  # Exact match on second document


@pytest.mark.asyncio
async def test_session_state_store_and_locks():
    store = TestSessionStateStore()
    session_id = "sess_test_1"

    await store.append_turn(session_id, {"speaker": "customer", "text": "Hi"})
    await store.append_turn(session_id, {"speaker": "agent", "text": "Hello"})

    window = await store.get_turn_window(session_id, limit=5)
    assert len(window) == 2
    assert window[0]["text"] == "Hi"

    # Distributed lock test
    lock_key = f"assist_lock:{session_id}"
    acquired = await store.acquire_lock(lock_key)
    assert acquired is True

    # Overlapping acquisition fails
    second_attempt = await store.acquire_lock(lock_key)
    assert second_attempt is False

    await store.release_lock(lock_key)
    re_acquired = await store.acquire_lock(lock_key)
    assert re_acquired is True


@pytest.mark.asyncio
async def test_pii_redactor():
    redactor = TestPIIRedactor()
    raw_text = "Customer card 4111 2222 3333 4444 and SSN 123-45-6789 reported issue."
    redacted = await redactor.redact(raw_text)
    assert "4111" not in redacted
    assert "123-45-6789" not in redacted
    assert "[REDACTED_PAN]" in redacted
    assert "[REDACTED_SSN]" in redacted


@pytest.mark.asyncio
async def test_blob_store():
    store = TestBlobStore()
    key = "audio/sample.pcm"
    data = b"\x00\x01\x02\x03"

    uri = await store.upload_bytes(key, data)
    assert "memory://" in uri

    exists = await store.exists(key)
    assert exists is True

    downloaded = await store.download_bytes(key)
    assert downloaded == data
