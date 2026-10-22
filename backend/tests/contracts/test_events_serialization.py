"""Unit tests for WebSocket event contracts and serialization compatibility."""

import json

import pytest
from pydantic import ValidationError

from app.contracts.events_v1 import (
    AssistRecommendationEvent,
    AudioChunkEvent,
    EventRole,
    EvidenceItemPayload,
    GroundingStatus,
    GuardrailAlertEvent,
    GuardrailSeverity,
    IntentCandidatePayload,
    IssueUpdateEvent,
    NextBestActionPayload,
    ProvenancePayload,
    SessionJoinEvent,
    SuggestedResponsePayload,
    SummaryReadyEvent,
    TranscriptFinalEvent,
    TranscriptPartialEvent,
    parse_event,
)


def test_session_join_serialization():
    event = SessionJoinEvent(
        session_id="sess_123",
        participant_id="part_cust_1",
        role=EventRole.CUSTOMER,
        auth_token="jwt.mock.token",
    )
    raw = event.model_dump_json()
    data = json.loads(raw)
    assert data["type"] == "session.join"
    assert data["session_id"] == "sess_123"
    assert data["role"] == "customer"
    assert data["auth_token"] == "jwt.mock.token"

    parsed = parse_event(data)
    assert isinstance(parsed, SessionJoinEvent)
    assert parsed.participant_id == "part_cust_1"


def test_audio_chunk_serialization():
    event = AudioChunkEvent(
        session_id="sess_123",
        participant_id="part_cust_1",
        role=EventRole.CUSTOMER,
        seq=42,
        sample_rate=16000,
        channels=1,
        format="pcm_s16le",
        payload_base64="AQIDBA==",
    )
    data = json.loads(event.model_dump_json())
    assert data["type"] == "audio.chunk"
    assert data["seq"] == 42
    assert data["sample_rate"] == 16000

    parsed = parse_event(data)
    assert isinstance(parsed, AudioChunkEvent)
    assert parsed.seq == 42


def test_transcript_events_serialization():
    partial = TranscriptPartialEvent(
        session_id="sess_123",
        turn_id=1,
        speaker=EventRole.CUSTOMER,
        text="I need help with",
    )
    data_partial = json.loads(partial.model_dump_json())
    assert data_partial["type"] == "transcript.partial"
    assert data_partial["is_final"] is False
    parsed_partial = parse_event(data_partial)
    assert isinstance(parsed_partial, TranscriptPartialEvent)

    final = TranscriptFinalEvent(
        session_id="sess_123",
        turn_id=1,
        speaker=EventRole.CUSTOMER,
        text="I need help with my debit card.",
        duration_ms=850.5,
    )
    data_final = json.loads(final.model_dump_json())
    assert data_final["type"] == "transcript.final"
    assert data_final["is_final"] is True
    parsed_final = parse_event(data_final)
    assert isinstance(parsed_final, TranscriptFinalEvent)
    assert parsed_final.duration_ms == 850.5


def test_issue_update_with_provenance():
    event = IssueUpdateEvent(
        session_id="sess_123",
        turn_id=2,
        intent_label="card_declined",
        confidence=0.96,
        is_out_of_scope=False,
        candidates=[
            IntentCandidatePayload(intent_label="card_declined", confidence=0.96),
            IntentCandidatePayload(intent_label="lost_card", confidence=0.03),
        ],
        exemplar_ids=["ex-01", "ex-02"],
        provenance=ProvenancePayload(
            model_version="gemma-3-1b-lora-v1",
            taxonomy_version="tx-14",
            corpus_version="kb-2026-10",
            prompt_version="prompt-v1.0",
        ),
    )
    data = json.loads(event.model_dump_json())
    assert data["type"] == "issue.update"
    assert data["provenance"]["model_version"] == "gemma-3-1b-lora-v1"
    assert data["provenance"]["taxonomy_version"] == "tx-14"

    parsed = parse_event(data)
    assert isinstance(parsed, IssueUpdateEvent)
    assert parsed.intent_label == "card_declined"
    assert len(parsed.candidates) == 2


def test_assist_recommendation_serialization():
    event = AssistRecommendationEvent(
        session_id="sess_123",
        turn_id=2,
        recommendations=[
            NextBestActionPayload(
                action_id="act-01",
                title="Verify Security Block",
                description="Check for velocity trigger",
                action_type="PROCEDURAL",
                steps=["Open Fraud Console", "Verify Card POS"],
                is_grounded=True,
                grounding_state=GroundingStatus.GROUNDED,
                citations=["POL-CARD-DECL-01"],
            )
        ],
        suggested_response=SuggestedResponsePayload(
            response_id="resp-01",
            text="I see a temporary security lock on your card.",
            rationale="Explains security block to customer.",
            is_editable=True,
            grounding_state=GroundingStatus.GROUNDED,
            citations=["POL-CARD-DECL-01"],
        ),
        evidence=[
            EvidenceItemPayload(
                chunk_id="POL-CARD-DECL-01",
                store_type="policy",
                title="Card Decline Policy",
                snippet="Automated security locks trigger on repeated POS attempts.",
                similarity_score=0.91,
            )
        ],
        grounding_state=GroundingStatus.GROUNDED,
    )
    data = json.loads(event.model_dump_json())
    assert data["type"] == "assist.recommendation"
    assert data["recommendations"][0]["action_type"] == "PROCEDURAL"
    assert data["evidence"][0]["chunk_id"] == "POL-CARD-DECL-01"

    parsed = parse_event(data)
    assert isinstance(parsed, AssistRecommendationEvent)
    assert parsed.grounding_state == GroundingStatus.GROUNDED


def test_guardrail_and_summary_events():
    alert = GuardrailAlertEvent(
        session_id="sess_123",
        turn_id=3,
        code="POLICY_REVIEW_NEEDED",
        message="No verified policy chunk supports fee waiver > $50",
        severity=GuardrailSeverity.WARNING,
    )
    data_alert = json.loads(alert.model_dump_json())
    assert data_alert["type"] == "guardrail.alert"
    assert data_alert["severity"] == "WARNING"

    summary = SummaryReadyEvent(
        session_id="sess_123",
        call_overview="Customer disputed overdraft fee.",
        key_issues=["Overdraft fee dispute"],
        actions_completed=["Processed $35 courtesy waiver"],
        required_followups=["Waiver reflects within 24h"],
        crm_case_note="CASE-12345: Waived $35 overdraft fee per policy.",
    )
    data_summary = json.loads(summary.model_dump_json())
    assert data_summary["type"] == "summary.ready"
    assert len(data_summary["key_issues"]) == 1

    parsed_summary = parse_event(data_summary)
    assert isinstance(parsed_summary, SummaryReadyEvent)
    assert parsed_summary.crm_case_note.startswith("CASE-12345")


def test_unknown_event_type_raises_validation_error():
    with pytest.raises(ValidationError):
        parse_event({"type": "unknown.event", "session_id": "123"})
