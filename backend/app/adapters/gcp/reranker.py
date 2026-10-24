"""GCP Vertex AI Ranking API adapter implementing Reranker port."""

from __future__ import annotations

import dataclasses
import logging
from typing import Any

from app.core.config import get_settings
from app.domain.evidence import EvidenceChunk

logger = logging.getLogger(__name__)


class VertexAIReranker:
    """Reranker port adapter connecting to GCP Vertex AI Ranking API (Discovery Engine)."""

    def __init__(
        self,
        project_id: str | None = None,
        ranking_config_name: str = "default_ranking_config",
        model: str = "semantic-ranker-512@latest",
    ) -> None:
        self.project_id = project_id
        self.ranking_config_name = ranking_config_name
        self.model = model
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from google.cloud import discoveryengine_v1 as discoveryengine

                self._client = discoveryengine.RankServiceClient()
            except Exception as e:
                logger.info(
                    "Vertex Ranking API client not available offline (%s). Using fallback scoring.",
                    e,
                )
        return self._client

    async def rerank(
        self,
        query: str,
        candidates: list[EvidenceChunk],
        top_k: int = 5,
    ) -> list[EvidenceChunk]:
        """Rerank candidate chunks using Vertex AI Ranking API or cross-encoder prior."""
        if not candidates:
            return []

        client = self._get_client()
        if client is not None:
            try:
                from google.cloud import discoveryengine_v1 as discoveryengine

                settings = get_settings()
                proj = self.project_id or getattr(settings, "GCP_PROJECT", "cc-agent-platform-dev")
                ranking_config = (
                    f"projects/{proj}/locations/global/rankingConfigs/{self.ranking_config_name}"
                )

                records = [
                    discoveryengine.RankingRecord(
                        id=chunk.chunk_id,
                        title=chunk.title,
                        content=chunk.text,
                    )
                    for chunk in candidates
                ]

                request = discoveryengine.RankRequest(
                    ranking_config=ranking_config,
                    model=self.model,
                    top_n=top_k,
                    query=query,
                    records=records,
                )

                response = client.rank(request=request)
                chunk_map = {c.chunk_id: c for c in candidates}
                reranked: list[EvidenceChunk] = []

                for record in response.records:
                    if record.id in chunk_map:
                        c = dataclasses.replace(
                            chunk_map[record.id], similarity_score=float(record.score)
                        )
                        reranked.append(c)

                if reranked:
                    return reranked
            except Exception as e:
                logger.warning("Vertex Ranking API call failed (%s). Using heuristic fallback.", e)

        # Deterministic offline fallback scoring
        query_terms = set(query.lower().split())
        scored: list[tuple[float, EvidenceChunk]] = []

        for c in candidates:
            content_lower = f"{c.title} {c.text}".lower()
            overlap = sum(1 for term in query_terms if term in content_lower)
            score = 0.5 + 0.1 * min(overlap, 5)
            updated_chunk = dataclasses.replace(c, similarity_score=round(score, 4))
            scored.append((score, updated_chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]
