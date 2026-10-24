"""Local Cross-Encoder Reranker Adapter (P5.3).

Connects to BAAI/bge-reranker-v2-m3 container with deterministic offline fallback scoring.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import re
import urllib.error
import urllib.request
from dataclasses import replace
from typing import Any

from app.domain.evidence import EvidenceChunk

logger = logging.getLogger(__name__)


class LocalReranker:
    """Reranker adapter connecting to local TEI cross-encoder with deterministic fallback."""

    def __init__(
        self,
        endpoint_url: str = "http://localhost:8002/rerank",
        timeout_seconds: float = 0.5,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.timeout_seconds = timeout_seconds

    async def rerank(
        self,
        query: str,
        candidates: list[EvidenceChunk],
        top_k: int = 5,
    ) -> list[EvidenceChunk]:
        """Rerank candidates using cross-encoder, falling back to offline scoring if unavailable."""
        if not candidates:
            return []

        if len(candidates) <= 1:
            return candidates[:top_k]

        try:
            return await self._rerank_remote(query, candidates, top_k)
        except Exception as e:
            logger.debug(
                f"Remote reranker at {self.endpoint_url} unavailable ({e}); using offline scoring."
            )
            return self._rerank_offline(query, candidates, top_k)

    async def _rerank_remote(
        self,
        query: str,
        candidates: list[EvidenceChunk],
        top_k: int,
    ) -> list[EvidenceChunk]:
        """Call TEI cross-encoder endpoint asynchronously."""
        texts = [f"{c.title}: {c.text}" for c in candidates]
        payload = {
            "query": query,
            "texts": texts,
            "truncate": True,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        loop = asyncio.get_running_loop()

        def _do_request() -> list[dict[str, Any]]:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result  # List of {"index": int, "score": float}

        scores = await loop.run_in_executor(None, _do_request)

        # Map scores back to chunks
        scored_chunks: list[EvidenceChunk] = []
        for item in scores:
            idx = item.get("index", 0)
            raw_score = float(item.get("score", 0.0))
            # Sigmoid normalize if needed
            norm_score = (
                1.0 / (1.0 + math.exp(-raw_score))
                if abs(raw_score) > 1.0
                else max(0.0, min(1.0, raw_score))
            )
            chunk = candidates[idx]
            scored_chunks.append(replace(chunk, similarity_score=round(norm_score, 4)))

        # Sort descending by updated score
        scored_chunks.sort(key=lambda c: c.similarity_score, reverse=True)
        return scored_chunks[:top_k]

    def _rerank_offline(
        self,
        query: str,
        candidates: list[EvidenceChunk],
        top_k: int,
    ) -> list[EvidenceChunk]:
        """Deterministic offline scoring based on lexical overlap, title match, and vector priors."""
        query_terms = set(re.findall(r"\w+", query.lower()))
        # Remove common stop words
        stops = {
            "i",
            "a",
            "the",
            "my",
            "was",
            "at",
            "to",
            "and",
            "in",
            "is",
            "of",
            "it",
            "on",
            "what",
            "how",
            "can",
        }
        salient_terms = {t for t in query_terms if t not in stops and len(t) > 2}

        scored: list[tuple[float, EvidenceChunk]] = []
        for chunk in candidates:
            chunk_text = f"{chunk.title} {chunk.text}".lower()
            chunk_tokens = set(re.findall(r"\w+", chunk_text))

            # Term overlap score
            if salient_terms:
                overlap = len(salient_terms & chunk_tokens) / len(salient_terms)
            else:
                overlap = 0.5

            # Procedural boost: Operational policy procedures (steps) have high utility for agents
            is_procedure = any(
                k in chunk_text
                for k in [
                    "step 1",
                    "step 2",
                    "procedure",
                    "authorization",
                    "resolution",
                    "protocol",
                ]
            )
            procedural_boost = 0.12 if is_procedure else 0.0

            # Title match boost
            title_tokens = set(re.findall(r"\w+", chunk.title.lower()))
            title_boost = 0.15 if (salient_terms & title_tokens) else 0.0

            # Intent label alignment
            chunk_intents = {lbl.lower().replace("_", " ") for lbl in chunk.intent_labels}
            intent_match = any(any(st in ci for st in salient_terms) for ci in chunk_intents)
            intent_boost = 0.15 if intent_match else 0.0

            # Blended cross-encoder proxy score: 40% vector/RRF prior + 35% lexical overlap + semantic boosts
            base_blend = (0.40 * chunk.similarity_score) + (0.35 * overlap)
            final_score = base_blend + title_boost + procedural_boost + intent_boost
            clamped_score = max(0.0, min(0.99, round(final_score, 4)))

            scored.append((clamped_score, replace(chunk, similarity_score=clamped_score)))

        # Sort descending by score
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [pair[1] for pair in scored[:top_k]]
