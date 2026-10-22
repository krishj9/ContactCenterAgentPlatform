"""Domain models for grounding decisions and compliance verification."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class GroundingState(StrEnum):
    """Grounding states enforced by the Deterministic Grounding State Machine."""

    GROUNDED = "GROUNDED"
    POLICY_REVIEW_NEEDED = "POLICY_REVIEW_NEEDED"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    UNGROUNDED = "UNGROUNDED"


@dataclass(frozen=True)
class GroundingDecision:
    """Deterministic grounding verification decision."""

    state: GroundingState
    policy_supported: bool
    matched_chunk_ids: list[str] = field(default_factory=list)
    entailment_score: float | None = None
    rejection_reason: str | None = None
    decided_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_grounded(self) -> bool:
        """Grounding Safety Invariant (R10, R13): Must have state GROUNDED and policy support."""
        return self.state == GroundingState.GROUNDED and self.policy_supported
