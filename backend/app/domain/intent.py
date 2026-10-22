"""Domain models for intent classification."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class IntentCandidate:
    """A scored intent candidate hypothesis."""

    intent_label: str
    confidence: float


@dataclass(frozen=True)
class IntentPrediction:
    """Fast-path intent classification hypothesis with calibrated confidence."""

    intent_label: str
    confidence: float
    candidate_intents: list[IntentCandidate] = field(default_factory=list)
    is_out_of_scope: bool = False
    model_version: str = "gemma-3-1b-lora-v1"
    taxonomy_version: str = "tx-14"
    explanation_exemplar_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_confident(self) -> bool:
        """Return True if confidence is high and intent is in-scope."""
        return not self.is_out_of_scope and self.confidence >= 0.70
