"""Versioned WebSocket Event Contracts (v1).

Pydantic v2 discriminated union models for all inbound and outbound WebSocket events.
All assist events strictly maintain provenance fields for auditability and replay.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# -----------------------------------------------------------------------------
# Base & Shared Structures
# -----------------------------------------------------------------------------


class EventRole(StrEnum):
    CUSTOMER = "customer"
    AGENT = "agent"
    SYSTEM = "system"


class GroundingStatus(StrEnum):
    GROUNDED = "GROUNDED"
    POLICY_REVIEW_NEEDED = "POLICY_REVIEW_NEEDED"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    UNGROUNDED = "UNGROUNDED"


class GuardrailSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ProvenancePayload(BaseModel):
    """Lineage metadata required across all assist payloads."""

    model_config = ConfigDict(extra="ignore")

    model_version: str = "gemma-3-1b-lora-v1"
    taxonomy_version: str = "tx-14"
    corpus_version: str = "kb-v1"
    prompt_version: str = "prompt-v1.0"


class CustomerContextPayload(BaseModel):
    """Customer CRM profile payload for session initialization."""

    model_config = ConfigDict(extra="ignore")

    customer_id: str
    name: str
    account_type: str
    relationship_tier: str
    account_number_masked: str
    context_summary: str
    extra: dict[str, Any] = Field(default_factory=dict)


class IntentCandidatePayload(BaseModel):
    """Scored candidate intent hypothesis."""

    intent_label: str
    confidence: float


class EvidenceItemPayload(BaseModel):
    """Retrieved evidence snippet citation."""

    chunk_id: str
    store_type: str  # "policy" | "faq"
    title: str
    snippet: str
    similarity_score: float
    source_uri: str | None = None
    risk_level: str | None = None


class NextBestActionPayload(BaseModel):
    """Actionable recommendation step for human agents."""

    action_id: str
    title: str
    description: str
    action_type: str  # "GUIDANCE" | "PROCEDURAL" | "COMPLIANCE" | "ESCALATION"
    steps: list[str]
    is_grounded: bool
    grounding_state: GroundingStatus
    citations: list[str] = Field(default_factory=list)


class SuggestedResponsePayload(BaseModel):
    """Conversational response suggestion draft."""

    response_id: str
    text: str
    rationale: str
    is_editable: bool = True
    grounding_state: GroundingStatus
    citations: list[str] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Inbound Events (Client -> Server)
# -----------------------------------------------------------------------------


class BaseEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    event_id: str = Field(default_factory=lambda: f"evt_{datetime.now(UTC).timestamp()}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SessionJoinEvent(BaseEvent):
    """Client authentication and joining a session."""

    type: Literal["session.join"] = "session.join"
    session_id: str
    participant_id: str
    role: EventRole
    auth_token: str | None = None


class AudioChunkEvent(BaseEvent):
    """Binary 16kHz mono PCM audio chunk envelope."""

    type: Literal["audio.chunk"] = "audio.chunk"
    session_id: str
    participant_id: str
    role: EventRole
    seq: int
    sample_rate: int = 16000
    channels: int = 1
    format: str = "pcm_s16le"
    payload_base64: str | None = None  # Base64-encoded PCM bytes if sent over JSON WS


class TranscriptManualEvent(BaseEvent):
    """Manual text input or scenario replay turn."""

    type: Literal["transcript.manual"] = "transcript.manual"
    session_id: str
    speaker: EventRole
    text: str


class SessionEndEvent(BaseEvent):
    """Client session termination."""

    type: Literal["session.end"] = "session.end"
    session_id: str
    reason: str = "hangup"


# -----------------------------------------------------------------------------
# Outbound Events (Server -> Client)
# -----------------------------------------------------------------------------


class SessionReadyEvent(BaseEvent):
    """Server confirmation that session is active and context is loaded."""

    type: Literal["session.ready"] = "session.ready"
    session_id: str
    participant_id: str
    role: EventRole
    status: str = "connected"
    customer_context: CustomerContextPayload | None = None


class TranscriptPartialEvent(BaseEvent):
    """Interim streaming transcription."""

    type: Literal["transcript.partial"] = "transcript.partial"
    session_id: str
    turn_id: int
    speaker: EventRole
    text: str
    is_final: Literal[False] = False


class TranscriptFinalEvent(BaseEvent):
    """Finalized utterance transcript segment."""

    type: Literal["transcript.final"] = "transcript.final"
    session_id: str
    turn_id: int
    speaker: EventRole
    text: str
    is_final: Literal[True] = True
    duration_ms: float = 0.0


class IssueUpdateEvent(BaseEvent):
    """Fast-path classified intent update (< 100ms)."""

    type: Literal["issue.update"] = "issue.update"
    session_id: str
    turn_id: int
    intent_label: str
    confidence: float
    is_out_of_scope: bool = False
    degraded: bool = False
    candidates: list[IntentCandidatePayload] = Field(default_factory=list)
    exemplar_ids: list[str] = Field(default_factory=list)
    provenance: ProvenancePayload = Field(default_factory=ProvenancePayload)


class AssistRecommendationEvent(BaseEvent):
    """Assist recommendations, next-best actions, and suggested response."""

    type: Literal["assist.recommendation"] = "assist.recommendation"
    session_id: str
    turn_id: int
    recommendations: list[NextBestActionPayload]
    suggested_response: SuggestedResponsePayload | None = None
    evidence: list[EvidenceItemPayload] = Field(default_factory=list)
    grounding_state: GroundingStatus
    provenance: ProvenancePayload = Field(default_factory=ProvenancePayload)


class GuardrailAlertEvent(BaseEvent):
    """Safety guardrail warning or suppression notice."""

    type: Literal["guardrail.alert"] = "guardrail.alert"
    session_id: str
    turn_id: int | None = None
    code: str  # e.g., "POLICY_REVIEW_NEEDED", "LOW_INTENT_CONFIDENCE", "MISSING_EVIDENCE"
    message: str
    severity: GuardrailSeverity = GuardrailSeverity.WARNING


class SummaryReadyEvent(BaseEvent):
    """Final post-call structured summary and CRM note draft."""

    type: Literal["summary.ready"] = "summary.ready"
    session_id: str
    call_overview: str
    key_issues: list[str]
    actions_completed: list[str]
    required_followups: list[str]
    crm_case_note: str
    provenance: ProvenancePayload = Field(default_factory=ProvenancePayload)


# -----------------------------------------------------------------------------
# Discriminated Unions
# -----------------------------------------------------------------------------

InboundEvent = Annotated[
    SessionJoinEvent | AudioChunkEvent | TranscriptManualEvent | SessionEndEvent,
    Field(discriminator="type"),
]

OutboundEvent = Annotated[
    SessionReadyEvent
    | TranscriptPartialEvent
    | TranscriptFinalEvent
    | IssueUpdateEvent
    | AssistRecommendationEvent
    | GuardrailAlertEvent
    | SummaryReadyEvent,
    Field(discriminator="type"),
]

WebSocketEvent = Annotated[
    SessionJoinEvent
    | AudioChunkEvent
    | TranscriptManualEvent
    | SessionEndEvent
    | SessionReadyEvent
    | TranscriptPartialEvent
    | TranscriptFinalEvent
    | IssueUpdateEvent
    | AssistRecommendationEvent
    | GuardrailAlertEvent
    | SummaryReadyEvent,
    Field(discriminator="type"),
]


class EventEnvelope(BaseModel):
    """Top-level parser envelope supporting discriminated union parsing."""

    event: WebSocketEvent


def parse_event(raw: dict[str, Any] | str | bytes) -> WebSocketEvent:
    """Parse raw JSON dict or string into strongly-typed WebSocketEvent."""
    if isinstance(raw, str | bytes):
        import json

        raw = json.loads(raw)
    parsed = EventEnvelope.model_validate({"event": raw})
    return parsed.event
