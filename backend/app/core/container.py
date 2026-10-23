"""Dependency injection container for ports and adapters."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, cast

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
from app.core.config import Settings, get_settings
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


class Container:
    """Dependency injection container resolving port protocols to profile-specific adapters."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._overrides: dict[str, Any] = {}

        # Profile-driven resolution (local | gcp | test)
        if self.settings.APP_PROFILE == "gcp":
            # Cloud Run / GCP profile (Vertex AI, Cloud SQL, Memorystore)
            # In Phase P1 test baseline, fallback to test adapters until P7 deployment
            self._intent_classifier: IntentClassifier = TestIntentClassifier()
            self._speech_to_text: SpeechToText = TestSpeechToText()
            self._embedder: Embedder = TestEmbedder()
            self._vector_index: VectorIndex = TestVectorIndex()
            self._document_store: DocumentStore = TestDocumentStore()
            self._reranker: Reranker = TestReranker()
            self._generator: Generator = TestGenerator()
            self._session_state_store: SessionStateStore = TestSessionStateStore()
            self._event_bus: EventBus = TestEventBus()
            self._blob_store: BlobStore = TestBlobStore()
            self._pii_redactor: PIIRedactor = TestPIIRedactor()
        else:
            # Default to test adapters for "test", "local", and fallback profiles
            self._intent_classifier = TestIntentClassifier()
            self._speech_to_text = TestSpeechToText()
            self._embedder = TestEmbedder()
            self._vector_index = TestVectorIndex()
            self._document_store = TestDocumentStore()
            self._reranker = TestReranker()
            self._generator = TestGenerator()
            self._session_state_store = TestSessionStateStore()
            self._event_bus = TestEventBus()
            self._blob_store = TestBlobStore()
            self._pii_redactor = TestPIIRedactor()

    @property
    def intent_classifier(self) -> IntentClassifier:
        return cast(
            IntentClassifier, self._overrides.get("intent_classifier", self._intent_classifier)
        )

    @property
    def speech_to_text(self) -> SpeechToText:
        return cast(SpeechToText, self._overrides.get("speech_to_text", self._speech_to_text))

    @property
    def embedder(self) -> Embedder:
        return cast(Embedder, self._overrides.get("embedder", self._embedder))

    @property
    def vector_index(self) -> VectorIndex:
        return cast(VectorIndex, self._overrides.get("vector_index", self._vector_index))

    @property
    def document_store(self) -> DocumentStore:
        return cast(DocumentStore, self._overrides.get("document_store", self._document_store))

    @property
    def reranker(self) -> Reranker:
        return cast(Reranker, self._overrides.get("reranker", self._reranker))

    @property
    def generator(self) -> Generator:
        return cast(Generator, self._overrides.get("generator", self._generator))

    @property
    def session_state_store(self) -> SessionStateStore:
        return cast(
            SessionStateStore, self._overrides.get("session_state_store", self._session_state_store)
        )

    @property
    def event_bus(self) -> EventBus:
        return cast(EventBus, self._overrides.get("event_bus", self._event_bus))

    @property
    def blob_store(self) -> BlobStore:
        return cast(BlobStore, self._overrides.get("blob_store", self._blob_store))

    @property
    def pii_redactor(self) -> PIIRedactor:
        return cast(PIIRedactor, self._overrides.get("pii_redactor", self._pii_redactor))

    def override(self, port_name: str, adapter: Any) -> None:
        """Override adapter for isolated unit testing."""
        self._overrides[port_name] = adapter

    def reset_overrides(self) -> None:
        """Clear all registered overrides."""
        self._overrides.clear()


@lru_cache
def get_container() -> Container:
    """Return cached DI container singleton."""
    return Container()
