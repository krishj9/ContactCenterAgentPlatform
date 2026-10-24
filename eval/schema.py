"""Evaluation and scenario fixture schemas for Contact Center Agent Assist."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class SpeakerRole(StrEnum):
    CUSTOMER = "customer"
    AGENT = "agent"
    SYSTEM = "system"


class GroundingState(StrEnum):
    GROUNDED = "GROUNDED"
    POLICY_REVIEW_NEEDED = "POLICY_REVIEW_NEEDED"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    UNGROUNDED = "UNGROUNDED"


class CustomerProfile(BaseModel):
    customer_id: str
    name: str
    account_type: str
    relationship_tier: str
    account_number_masked: str
    context_summary: str
    extra: dict[str, Any] = Field(default_factory=dict)


class ScenarioTurn(BaseModel):
    turn_id: int
    speaker: SpeakerRole
    text: str
    expected_intent: str | None = None
    expected_confidence_min: float | None = None
    expected_grounding_state: GroundingState | None = None
    required_citations: list[str] = Field(default_factory=list)
    suggested_response_keywords: list[str] = Field(default_factory=list)


class ExpectedSummary(BaseModel):
    call_overview: str
    key_issues: list[str] = Field(default_factory=list)
    actions_completed: list[str] = Field(default_factory=list)
    required_followups: list[str] = Field(default_factory=list)


class ScenarioFixture(BaseModel):
    scenario_id: str
    title: str
    description: str
    customer_profile: CustomerProfile
    turns: list[ScenarioTurn]
    expected_summary: ExpectedSummary | None = None
    tags: list[str] = Field(default_factory=list)


def load_scenario_fixture(path: Path | str) -> ScenarioFixture:
    """Load and validate a ScenarioFixture JSON file."""
    import json
    from pathlib import Path

    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return ScenarioFixture.model_validate(data)
