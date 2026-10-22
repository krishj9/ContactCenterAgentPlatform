"""Test adapter for Reranker port."""

from __future__ import annotations

from app.domain.evidence import EvidenceChunk


class TestReranker:
    """Deterministic reranker prioritizing exact token matches and policy sources."""

    __test__ = False

    async def rerank(
        self,
        query: str,
        candidates: list[EvidenceChunk],
        top_k: int = 5,
    ) -> list[EvidenceChunk]:
        query_terms = set(query.lower().split())

        def score(chunk: EvidenceChunk) -> float:
            text_terms = set(chunk.text.lower().split())
            overlap = len(query_terms.intersection(text_terms))
            # Policy chunks receive slight priority per Grounding Safety rules
            bonus = 1.0 if chunk.is_policy else 0.0
            return chunk.similarity_score + overlap * 0.1 + bonus

        ranked = sorted(candidates, key=score, reverse=True)
        return ranked[:top_k]
