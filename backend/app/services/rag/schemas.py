"""Structured RAG Generation Output Schemas (P5.5, Spec §3.3.2).

Enforces strict JSON schema generation for Next-Best Actions and Suggested Responses.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class NextBestActionItem(BaseModel):
    """Actionable operational guidance step for the human agent (Spec §3.3.2)."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(description="Short imperative action title.")
    steps: list[str] = Field(description="Step-by-step procedure items.")
    citations: list[str] = Field(
        min_length=1,
        description="Exact chunk IDs supporting this action (e.g. 'pol_card_decline_01_s4_c1').",
    )
    action_type: Literal["verify", "inform", "escalate"] = Field(
        description="Action classification pill (verify | inform | escalate)."
    )


class SuggestedResponseItem(BaseModel):
    """Editable conversational response draft for the agent to say (Spec §3.3.2)."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(
        description="Conversational reply in agent voice (<= 60 words, never promising unauthorized reversals)."
    )
    citations: list[str] = Field(
        default_factory=list,
        description="Chunk IDs supporting the response statement.",
    )


class RAGGenerationOutput(BaseModel):
    """Schema-constrained generation contract for Ollama / Gemini (Spec §3.3.2)."""

    model_config = ConfigDict(extra="forbid")

    next_best_actions: list[NextBestActionItem] = Field(
        default_factory=list,
        description="List of verified next-best actions.",
    )
    suggested_response: SuggestedResponseItem | None = Field(
        default=None,
        description="Suggested conversational response draft.",
    )
    abstain: bool = Field(
        default=False,
        description="True if evidence is insufficient to ground an operational response.",
    )
    abstain_reason: str | None = Field(
        default=None,
        description="Reason for abstaining if abstain is True.",
    )
