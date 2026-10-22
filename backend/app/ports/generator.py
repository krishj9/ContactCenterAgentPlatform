"""Port protocol for LLM structured generation."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from app.domain.evidence import EvidenceChunk
from app.domain.intent import IntentPrediction
from app.domain.recommendation import NextBestAction, SuggestedResponse
from app.domain.summary import CallSummary


@runtime_checkable
class Generator(Protocol):
    """Protocol for schema-constrained LLM generation (next-best actions and summaries)."""

    async def generate_action(
        self,
        intent: IntentPrediction,
        evidence: list[EvidenceChunk],
        customer_context: dict[str, Any] | None = None,
    ) -> tuple[NextBestAction, SuggestedResponse]:
        """Generate a next-best action and suggested response draft citing retrieved evidence."""
        ...

    async def generate_summary(
        self,
        session_id: str,
        transcript_turns: list[dict[str, Any]],
    ) -> CallSummary:
        """Generate structured post-call summary and CRM case note."""
        ...
