"""Unit tests for domain models and grounding safety invariants."""

from app.domain.grounding import GroundingDecision, GroundingState
from app.domain.intent import IntentCandidate, IntentPrediction
from app.domain.recommendation import (
    ActionType,
    NextBestAction,
    SuggestedResponse,
)
from app.domain.summary import CallSummary


def test_intent_prediction_confidence_and_oos():
    pred_in_scope = IntentPrediction(
        intent_label="card_declined",
        confidence=0.95,
        candidate_intents=[IntentCandidate("card_declined", 0.95)],
    )
    assert pred_in_scope.is_confident is True
    assert pred_in_scope.is_out_of_scope is False

    pred_oos = IntentPrediction(
        intent_label="out_of_scope",
        confidence=0.90,
        is_out_of_scope=True,
    )
    assert pred_oos.is_confident is False


def test_grounding_safety_invariant_r10_r13():
    """Grounding Safety Invariant (R10, R13):

    No operational recommendation may be considered grounded without supporting policy evidence.
    """
    # GROUNDED state but policy_supported is False -> NOT grounded
    invalid_grounding = GroundingDecision(
        state=GroundingState.GROUNDED,
        policy_supported=False,
        matched_chunk_ids=[],
    )
    assert invalid_grounding.is_grounded is False

    # Proper grounded state with policy support
    valid_grounding = GroundingDecision(
        state=GroundingState.GROUNDED,
        policy_supported=True,
        matched_chunk_ids=["POL-FEE-01"],
        entailment_score=0.95,
    )
    assert valid_grounding.is_grounded is True


def test_next_best_action_and_suggested_response():
    grounding = GroundingDecision(
        state=GroundingState.GROUNDED,
        policy_supported=True,
        matched_chunk_ids=["POL-CARD-01"],
    )
    action = NextBestAction(
        action_id="act-01",
        title="Clear Card Lock",
        description="Verify and lift security block",
        action_type=ActionType.PROCEDURAL,
        steps=["Step 1", "Step 2"],
        grounding=grounding,
        citations=["POL-CARD-01"],
    )
    assert action.is_grounded is True
    assert action.action_type == ActionType.PROCEDURAL
    assert len(action.citations) == 1

    response = SuggestedResponse(
        response_id="resp-01",
        text="I can assist with unlocking your card.",
        rationale="Clear lock for customer",
        grounding=grounding,
        citations=["POL-CARD-01"],
        is_editable=True,
    )
    assert response.is_editable is True
    assert response.provenance.model_version == "gemma-3-flash-v1"


def test_call_summary_structure():
    summary = CallSummary(
        summary_id="sum-01",
        session_id="sess-01",
        call_overview="Customer disputed charge.",
        key_issues=["Duplicate charge of $248.50"],
        actions_completed=["Filed dispute claim"],
        required_followups=["30-day merchant resolution"],
        crm_case_note="CASE-01: Dispute claim filed.",
    )
    assert summary.summary_id == "sum-01"
    assert len(summary.actions_completed) == 1
    assert summary.crm_case_note.startswith("CASE-01")
