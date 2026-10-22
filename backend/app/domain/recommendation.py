"""Domain models for next-best actions and suggested agent responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from app.domain.grounding import GroundingDecision


class ActionType(StrEnum):
    """Categorization for next-best action steps."""

    GUIDANCE = "GUIDANCE"
    PROCEDURAL = "PROCEDURAL"
    COMPLIANCE = "COMPLIANCE"
    ESCALATION = "ESCALATION"


@dataclass(frozen=True)
class Provenance:
    """Lineage metadata for reproducibility and auditing."""

    model_version: str = "gemma-3-flash-v1"
    taxonomy_version: str = "tx-14"
    corpus_version: str = "kb-v1"
    prompt_version: str = "prompt-v1.0"


@dataclass(frozen=True)
class NextBestAction:
    """Actionable, human-in-the-loop recommendation card for the human agent."""

    action_id: str
    title: str
    description: str
    action_type: ActionType
    steps: list[str]
    grounding: GroundingDecision
    citations: list[str] = field(default_factory=list)
    confidence: float = 0.90
    provenance: Provenance = field(default_factory=Provenance)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_grounded(self) -> bool:
        return self.grounding.is_grounded


@dataclass(frozen=True)
class SuggestedResponse:
    """Editable conversational response ready for the agent to say or adapt."""

    response_id: str
    text: str
    rationale: str
    grounding: GroundingDecision
    citations: list[str] = field(default_factory=list)
    is_editable: bool = True
    provenance: Provenance = field(default_factory=Provenance)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
