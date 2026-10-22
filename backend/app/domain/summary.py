"""Domain models for structured post-call summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.recommendation import Provenance


@dataclass(frozen=True)
class CallSummary:
    """Post-call summary draft with CRM case note integration."""

    summary_id: str
    session_id: str
    call_overview: str
    key_issues: list[str] = field(default_factory=list)
    actions_completed: list[str] = field(default_factory=list)
    required_followups: list[str] = field(default_factory=list)
    crm_case_note: str = ""
    provenance: Provenance = field(default_factory=Provenance)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
