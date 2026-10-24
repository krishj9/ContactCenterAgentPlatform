"""Store Router and Parallel Retrieval with Filter-Relax Retry (P5.2).

Dispatches hybrid search across policy and faq stores with automatic intent filtering
and filter-relax retry on empty matches (Spec §3.3.2).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from app.domain.evidence import EvidenceChunk
from app.ports.document_store import DocumentStore
from app.ports.embedder import Embedder
from app.ports.vector_index import VectorIndex
from app.services.rag.query_builder import BuiltQuery

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StoreRetrievalResult:
    """Consolidated retrieval result across logical stores."""

    policy_chunks: list[EvidenceChunk]
    faq_chunks: list[EvidenceChunk]
    filter_relaxed: bool = False
    all_chunks: list[EvidenceChunk] = field(default_factory=list)

    @property
    def has_policy(self) -> bool:
        return len(self.policy_chunks) > 0

    @property
    def has_evidence(self) -> bool:
        return len(self.all_chunks) > 0


class StoreRouter:
    """Coordinates parallel vector search and document hydration with filter relaxation."""

    def __init__(
        self,
        embedder: Embedder,
        vector_index: VectorIndex,
        document_store: DocumentStore,
        config_path: Path | str | None = None,
    ) -> None:
        self.embedder = embedder
        self.vector_index = vector_index
        self.document_store = document_store

        if config_path:
            self.config_path = Path(config_path)
        else:
            candidates = [
                Path("config/retrieval_routes.yaml"),
                Path(__file__).resolve().parents[4] / "config" / "retrieval_routes.yaml",
                Path(__file__).resolve().parents[3] / "config" / "retrieval_routes.yaml",
            ]
            self.config_path = next((c for c in candidates if c.exists()), candidates[1])
        self.routes_config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        if self.config_path.exists():
            with open(self.config_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    async def route_and_retrieve(
        self,
        query: BuiltQuery,
        top_k_policy: int = 20,
        top_k_faq: int = 10,
    ) -> StoreRetrievalResult:
        """Execute parallel hybrid retrieval across stores with filter relaxation retry."""
        # Check out-of-scope intent
        if query.intent_label == "out_of_scope":
            logger.info("Intent is out_of_scope; bypassing operational policy retrieval.")
            return StoreRetrievalResult(policy_chunks=[], faq_chunks=[], filter_relaxed=False)

        # 1. Compute dense query embedding vector
        query_vector = await self.embedder.embed_query(query.query_text)

        # 2. Prepare intent filters
        intent_filter = {"intent": query.intent_label}

        # 3. Parallel dispatch across policy and FAQ stores
        policy_coro = self._retrieve_and_hydrate(
            store_type="policy",
            query_vector=query_vector,
            top_k=top_k_policy,
            filters=intent_filter,
        )
        faq_coro = self._retrieve_and_hydrate(
            store_type="faq",
            query_vector=query_vector,
            top_k=top_k_faq,
            filters=intent_filter,
        )

        policy_chunks, faq_chunks = await asyncio.gather(policy_coro, faq_coro)
        filter_relaxed = False

        # 4. Filter-relax retry (Spec §3.3.2):
        # If intent requires policy and filtered policy search yielded 0 results, retry without filter
        if query.requires_policy and not policy_chunks:
            logger.warning(
                f"Policy search with intent filter '{query.intent_label}' returned 0 chunks. "
                "Retrying with relaxed filter."
            )
            policy_chunks = await self._retrieve_and_hydrate(
                store_type="policy",
                query_vector=query_vector,
                top_k=top_k_policy,
                filters=None,
            )
            filter_relaxed = True

        # Combine all candidates
        combined = list(policy_chunks) + list(faq_chunks)

        return StoreRetrievalResult(
            policy_chunks=policy_chunks,
            faq_chunks=faq_chunks,
            filter_relaxed=filter_relaxed,
            all_chunks=combined,
        )

    async def _retrieve_and_hydrate(
        self,
        store_type: str,
        query_vector: list[float],
        top_k: int,
        filters: dict[str, Any] | None,
    ) -> list[EvidenceChunk]:
        """Query vector index and hydrate chunks from document store."""
        search_hits = await self.vector_index.search(
            store_type=store_type,
            query_vector=query_vector,
            top_k=top_k,
            filters=filters,
        )
        if not search_hits:
            return []

        doc_ids = [hit[0] for hit in search_hits]
        score_map = {hit[0]: hit[1] for hit in search_hits}

        docs = await self.document_store.get_many(doc_ids)
        evidence_chunks: list[EvidenceChunk] = []

        for doc in docs:
            chunk_id = doc.get("id") or doc.get("chunk_id", "")
            if not chunk_id:
                continue
            sim_score = score_map.get(chunk_id, 0.0)
            evidence_chunks.append(
                EvidenceChunk(
                    chunk_id=chunk_id,
                    store_type=store_type,
                    title=doc.get("title", f"{store_type.title()} Chunk"),
                    text=doc.get("text", ""),
                    similarity_score=sim_score,
                    intent_labels=doc.get("intent_labels", []),
                    corpus_version=doc.get("corpus_version", "kb-v1"),
                    source_uri=doc.get("source_uri"),
                    risk_level=doc.get("risk_level", "medium"),
                )
            )

        # Sort descending by similarity score
        evidence_chunks.sort(key=lambda c: c.similarity_score, reverse=True)
        return evidence_chunks
