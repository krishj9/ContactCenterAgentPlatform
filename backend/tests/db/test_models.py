"""Unit tests validating SQLAlchemy ORM models and schema invariants."""

from app.db.models import (
    FeedbackEventModel,
    IssuePredictionModel,
    KBChunkModel,
    ParticipantModel,
    RecommendationModel,
    RecommendationSourceModel,
    ResponseSuggestionModel,
    SessionModel,
    SummaryModel,
    TranscriptSegmentModel,
)


def test_session_and_participant_models() -> None:
    session = SessionModel(
        session_id="sess_test_101",
        status="active",
        customer_id="cust_001",
        customer_metadata={"tier": "Platinum", "name": "Sarah Jenkins"},
    )
    assert session.session_id == "sess_test_101"
    assert session.customer_metadata is not None
    assert session.customer_metadata["tier"] == "Platinum"

    participant = ParticipantModel(
        participant_id="part_agent_1",
        session_id=session.session_id,
        role="agent",
    )
    assert participant.participant_id == "part_agent_1"
    assert participant.role == "agent"


def test_transcript_segment_model() -> None:
    segment = TranscriptSegmentModel(
        session_id="sess_test_101",
        turn_id=1,
        speaker="customer",
        text="My card was declined in Paris.",
        is_final=True,
        duration_ms=1450.5,
    )
    assert segment.turn_id == 1
    assert segment.speaker == "customer"
    assert segment.duration_ms == 1450.5


def test_issue_prediction_model() -> None:
    prediction = IssuePredictionModel(
        session_id="sess_test_101",
        turn_id=1,
        intent_label="card_declined",
        confidence=0.94,
        is_out_of_scope=False,
        model_version="gemma-3-1b-lora-v1",
        taxonomy_version="tx-14",
    )
    assert prediction.intent_label == "card_declined"
    assert prediction.confidence == 0.94


def test_recommendation_and_source_models() -> None:
    rec = RecommendationModel(
        session_id="sess_test_101",
        turn_id=1,
        action_id="act_lift_hold",
        title="Lift Geographic Decline",
        description="Lift temporary fraud hold for Paris POS terminal",
        grounding_state="GROUNDED",
        model_version="gemma-3-1b-lora-v1",
        corpus_version="corpus-v2",
        prompt_version="prompt-nba-v1",
    )
    source = RecommendationSourceModel(
        recommendation_id=1,
        chunk_id="POL-CARD-DECLINE-01",
        store_type="policy",
        similarity_score=0.89,
        title="Card Decline Policy",
    )
    assert rec.action_id == "act_lift_hold"
    assert rec.grounding_state == "GROUNDED"
    assert source.chunk_id == "POL-CARD-DECLINE-01"


def test_response_suggestion_model() -> None:
    suggestion = ResponseSuggestionModel(
        session_id="sess_test_101",
        turn_id=1,
        response_id="resp_01",
        text="I have lifted the temporary hold on your card, Sarah.",
        rationale="Account verified and foreign transaction approved.",
        is_editable=True,
        grounding_state="GROUNDED",
        citations=["POL-CARD-DECLINE-01"],
        model_version="gemma-3-1b-lora-v1",
    )
    assert suggestion.response_id == "resp_01"
    assert suggestion.is_editable is True
    assert "POL-CARD-DECLINE-01" in suggestion.citations


def test_summary_and_feedback_models() -> None:
    summary = SummaryModel(
        session_id="sess_test_101",
        call_overview="Customer experienced card decline abroad.",
        key_issues=["card_declined"],
        actions_completed=["fraud_hold_lifted", "travel_notice_added"],
        required_followups=[],
        crm_case_note="Customer advised card is operational.",
        model_version="gemma-3-1b-lora-v1",
    )
    assert summary.session_id == "sess_test_101"
    assert len(summary.actions_completed) == 2

    feedback = FeedbackEventModel(
        session_id="sess_test_101",
        item_type="recommendation",
        item_id="act_lift_hold",
        agent_disposition="accepted",
        comment="Accurate guidance.",
    )
    assert feedback.agent_disposition == "accepted"


def test_kb_chunk_model() -> None:
    chunk = KBChunkModel(
        chunk_id="POL-CARD-DECLINE-01",
        store_type="policy",
        intent_label="card_declined",
        title="Card Decline Policy Procedure",
        text="Procedures for handling point-of-sale card declines.",
        token_count=120,
        status="active",
        version_tag="v1",
    )
    assert chunk.chunk_id == "POL-CARD-DECLINE-01"
    assert chunk.store_type == "policy"
    assert chunk.status == "active"
