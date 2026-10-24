"""Unit tests for GCP port adapters (P7.9, P7.10).

Validates protocol conformance, offline fallback resiliency, and DI container wiring under APP_PROFILE=gcp.
"""

from __future__ import annotations

import pytest

from app.adapters.gcp.embedder import VertexAIEmbedder
from app.adapters.gcp.generator import VertexAIGeminiGenerator
from app.adapters.gcp.pgvector_index import CloudSQLPgVectorIndex
from app.adapters.gcp.reranker import VertexAIReranker
from app.adapters.gcp.speech_to_text import GoogleCloudSTT
from app.core.config import Settings
from app.core.container import Container
from app.domain.evidence import EvidenceChunk
from app.domain.intent import IntentCandidate, IntentPrediction
from app.ports.embedder import Embedder
from app.ports.generator import Generator
from app.ports.reranker import Reranker
from app.ports.speech_to_text import SpeechToText
from app.ports.vector_index import VectorIndex


class TestGcpAdaptersProtocolConformance:
    """Verify all GCP adapters satisfy port protocols."""

    def test_embedder_conformance(self) -> None:
        adapter = VertexAIEmbedder(dimension=768)
        assert isinstance(adapter, Embedder)
        assert adapter.dim == 768

    def test_vector_index_conformance(self) -> None:
        adapter = CloudSQLPgVectorIndex()
        assert isinstance(adapter, VectorIndex)

    def test_reranker_conformance(self) -> None:
        adapter = VertexAIReranker()
        assert isinstance(adapter, Reranker)

    def test_generator_conformance(self) -> None:
        adapter = VertexAIGeminiGenerator()
        assert isinstance(adapter, Generator)

    def test_speech_to_text_conformance(self) -> None:
        adapter = GoogleCloudSTT()
        assert isinstance(adapter, SpeechToText)


@pytest.mark.asyncio
class TestVertexAIEmbedderOffline:
    """Test VertexAIEmbedder dense embedding offline fallback."""

    async def test_embed_texts_offline(self) -> None:
        embedder = VertexAIEmbedder(dimension=768)
        texts = ["Card declined at grocery store", "International travel notification"]
        vectors = await embedder.embed_texts(texts)

        assert len(vectors) == 2
        assert len(vectors[0]) == 768
        assert len(vectors[1]) == 768
        norm0 = sum(x * x for x in vectors[0]) ** 0.5
        assert pytest.approx(norm0, rel=1e-3) == 1.0

    async def test_embed_query_offline(self) -> None:
        embedder = VertexAIEmbedder(dimension=768)
        vec = await embedder.embed_query("why was my card declined?")
        assert len(vec) == 768


@pytest.mark.asyncio
class TestVertexAIRerankerOffline:
    """Test VertexAIReranker scoring and top-k selection offline."""

    async def test_rerank_candidates_offline(self) -> None:
        reranker = VertexAIReranker()
        query = "card lost stolen freeze"
        candidates = [
            EvidenceChunk(
                chunk_id="pol_001",
                store_type="policy",
                title="International Travel Guidance",
                text="Notify us before traveling abroad to ensure continuous card access.",
                similarity_score=0.6,
            ),
            EvidenceChunk(
                chunk_id="pol_002",
                store_type="policy",
                title="Lost or Stolen Card Reporting and Temporary Freeze",
                text="Customers reporting a lost or stolen card must immediately freeze their card in the app.",
                similarity_score=0.7,
            ),
        ]

        reranked = await reranker.rerank(query=query, candidates=candidates, top_k=2)
        assert len(reranked) == 2
        # pol_002 has high keyword overlap with query (card, lost, stolen, freeze)
        assert reranked[0].chunk_id == "pol_002"
        assert reranked[0].similarity_score > reranked[1].similarity_score


@pytest.mark.asyncio
class TestVertexAIGeminiGeneratorOffline:
    """Test VertexAIGeminiGenerator fallback execution."""

    async def test_generate_action_fallback(self) -> None:
        generator = VertexAIGeminiGenerator()
        intent = IntentPrediction(
            intent_label="card_declined",
            confidence=0.92,
            candidate_intents=[IntentCandidate(intent_label="card_declined", confidence=0.92)],
        )
        evidence = [
            EvidenceChunk(
                chunk_id="pol_declined_001",
                store_type="policy",
                title="Declined Card Protocol",
                text="Check for fraud blocks, insufficient funds, or incorrect PIN entries.",
                similarity_score=0.88,
            )
        ]

        action, response = await generator.generate_action(
            intent=intent,
            evidence=evidence,
            customer_context={"customer_id": "cust_123"},
        )

        assert action.action_id.startswith("act_")
        assert len(action.steps) > 0
        assert action.grounding.policy_supported is True
        assert "pol_declined_001" in action.citations
        assert response.response_id.startswith("resp_")
        assert len(response.text) > 0

    async def test_generate_summary_offline(self) -> None:
        generator = VertexAIGeminiGenerator()
        turns = [
            {"speaker": "customer", "text": "Hi, my debit card was declined at an ATM."},
            {"speaker": "agent", "text": "Let me help you check your account status."},
            {"speaker": "customer", "text": "Thank you, I need this resolved right away."},
        ]

        summary = await generator.generate_summary(
            session_id="sess_test_gcp", transcript_turns=turns
        )
        assert summary.session_id == "sess_test_gcp"
        assert "ATM" in summary.call_overview or "inquiry" in summary.call_overview
        assert len(summary.actions_completed) > 0
        assert "CRM CASE NOTE" in summary.crm_case_note


@pytest.mark.asyncio
class TestCloudSQLPgVectorIndexOffline:
    """Test CloudSQLPgVectorIndex offline fallback operations."""

    async def test_upsert_and_search_fallback(self) -> None:
        index = CloudSQLPgVectorIndex()
        ids = ["c_001", "c_002"]
        vectors = [[0.1] * 768, [0.2] * 768]
        metas = [
            {"title": "Chunk 1", "intent_label": "card_declined"},
            {"title": "Chunk 2", "intent_label": "pin_change"},
        ]

        await index.upsert("policy", ids, vectors, metas)
        hits = await index.search("policy", [0.1] * 768, top_k=2)
        assert len(hits) == 2
        assert hits[0][0] in ids
        await index.close()


@pytest.mark.asyncio
class TestGoogleCloudSTTOffline:
    """Test GoogleCloudSTT streaming and chunk transcription."""

    async def test_transcribe_chunk_offline(self) -> None:
        stt = GoogleCloudSTT()
        # 1600 bytes of silence (100ms at 16kHz 16-bit mono)
        silent_pcm = b"\x00" * 1600
        text = await stt.transcribe_chunk(silent_pcm, is_final=True)
        assert isinstance(text, str)

    async def test_transcribe_stream_offline(self) -> None:
        import math
        import struct

        stt = GoogleCloudSTT()

        # Generate audio with speech energy (440Hz sine wave, amplitude 5000)
        samples = [int(5000 * math.sin(2 * math.pi * 440 * i / 16000)) for i in range(9600)]
        active_pcm = struct.pack(f"<{len(samples)}h", *samples)
        silent_pcm = b"\x00" * 16000

        async def audio_gen():
            yield active_pcm
            yield silent_pcm

        results = []
        async for transcript, is_final in stt.transcribe_stream(audio_gen(), "s1", "p1"):
            results.append((transcript, is_final))
        assert len(results) > 0
        assert any(is_final for _, is_final in results)


class TestContainerGcpProfileWiring:
    """Verify Container properly wires GCP adapters when APP_PROFILE=gcp."""

    def test_container_gcp_wiring(self) -> None:
        settings = Settings(
            APP_PROFILE="gcp",
            GCP_PROJECT="test-gcp-project",
            GCP_REGION="us-central1",
        )
        container = Container(settings=settings)

        assert isinstance(container.embedder, VertexAIEmbedder)
        assert isinstance(container.vector_index, CloudSQLPgVectorIndex)
        assert isinstance(container.reranker, VertexAIReranker)
        assert isinstance(container.generator, VertexAIGeminiGenerator)
        assert isinstance(container.speech_to_text, GoogleCloudSTT)
