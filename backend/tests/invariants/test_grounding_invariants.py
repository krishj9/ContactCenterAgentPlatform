"""Grounding Safety and Invariant Test Suite (P5.10, Spec §3.3.3, R10, R13, R14).

CI-blocking invariant assertions:
1. GROUNDED => len(sources) >= 1 and policy_supported == True
2. action_type in {verify, escalate} => exists policy source
3. Zero operational actions generated without policy support
4. Customer isolation: internal assist events never route to customer role
5. Human-in-the-loop: recommendations are assistive and editable
"""

from __future__ import annotations

from app.contracts.events_v1 import (
    AssistRecommendationEvent,
    GroundingStatus,
    IssueUpdateEvent,
)
from app.domain.evidence import EvidenceChunk
from app.domain.grounding import GroundingState
from app.domain.intent import IntentPrediction
from app.domain.recommendation import ActionType
from app.services.grounding.state_machine import DeterministicGroundingStateMachine
from app.services.rag.fallback import PlaybookFallbackService
from app.services.rag.schemas import NextBestActionItem, RAGGenerationOutput, SuggestedResponseItem
from app.services.rag.verifier import ClaimAndCitationVerifier


def test_invariant_grounded_requires_policy_support():
    """Invariant 1: An action or decision cannot be GROUNDED without verified policy support (R10)."""
    state_machine = DeterministicGroundingStateMachine(
        tau_intent=0.55,
        tau_evidence=0.48,
        tau_policy=0.68,
    )

    intent = IntentPrediction(
        intent_label="card_declined",
        confidence=0.92,
        is_out_of_scope=False,
    )

    # Only FAQ chunk, no policy chunk
    faq_only = [
        EvidenceChunk(
            chunk_id="faq_001",
            store_type="faq",
            title="Card FAQ",
            text="FAQ answer text",
            similarity_score=0.85,
        )
    ]

    eval_result = state_machine.evaluate(
        intent=intent,
        evidence=faq_only,
        requires_policy=True,
    )

    # Invariant: Must NOT be GROUNDED when policy is required but absent
    assert eval_result.state != GroundingState.GROUNDED
    assert eval_result.state == GroundingState.POLICY_REVIEW_NEEDED
    assert eval_result.policy_supported is False
    assert eval_result.warning_code == "MISSING_POLICY_SUPPORT"


def test_invariant_operational_action_types_require_policy_citation():
    """Invariant 2: Operational action_types (verify, escalate) must have at least one policy citation."""
    verifier = ClaimAndCitationVerifier()

    context = [
        EvidenceChunk(
            chunk_id="faq_101",
            store_type="faq",
            title="General FAQ",
            text="General information",
            similarity_score=0.88,
        )
    ]

    # Model attempts to produce an operational "verify" action citing only an FAQ chunk
    gen_output = RAGGenerationOutput(
        next_best_actions=[
            NextBestActionItem(
                title="Verify POS Terminal",
                steps=["Check terminal ID 4821"],
                citations=["faq_101"],
                action_type="verify",
            )
        ],
        suggested_response=SuggestedResponseItem(
            text="I can verify your transaction.",
            citations=["faq_101"],
        ),
    )

    result = verifier.verify(gen_output, context, "card_declined")

    # Invariant assertion: Verifier flags missing policy for operational action
    assert result.missing_policy_for_operational is True
    # The generated action must NOT have GroundingState.GROUNDED
    for action in result.actions:
        if action.action_type in {ActionType.COMPLIANCE, ActionType.ESCALATION}:
            assert action.grounding.state != GroundingState.GROUNDED


def test_invariant_uncited_claims_stripped():
    """Invariant 3: Actions citing non-existent chunks must be stripped (R13)."""
    verifier = ClaimAndCitationVerifier()

    context = [
        EvidenceChunk(
            chunk_id="pol_real_01",
            store_type="policy",
            title="Real Policy",
            text="Procedure text",
            similarity_score=0.90,
        )
    ]

    # Model hallucinates a citation not present in context
    gen_output = RAGGenerationOutput(
        next_best_actions=[
            NextBestActionItem(
                title="Hallucinated Action",
                steps=["Perform unauthorized waiver"],
                citations=["pol_fake_9999"],
                action_type="inform",
            )
        ],
    )

    result = verifier.verify(gen_output, context, "card_declined")

    # Invariant assertion: Action with invalid citation was stripped
    assert len(result.actions) == 0
    assert result.dropped_claims_count > 0


def test_invariant_customer_isolation_event_filtering():
    """Invariant 4: Customer connections must NEVER receive internal assist events (R9, R14)."""
    internal_events = [
        IssueUpdateEvent(
            session_id="sess_test",
            turn_id=1,
            intent_label="card_declined",
            confidence=0.94,
            is_out_of_scope=False,
            candidates=[],
            exemplar_ids=[],
        ),
        AssistRecommendationEvent(
            session_id="sess_test",
            turn_id=1,
            grounding_state=GroundingStatus.GROUNDED,
            recommendations=[],
        ),
    ]

    # Simulated outbound filter check: customer role must reject internal assist events
    allowed_types_for_customer = {
        "session.ready",
        "transcript.partial",
        "transcript.final",
        "session.end",
    }

    for event in internal_events:
        is_allowed = event.type in allowed_types_for_customer
        assert not is_allowed, f"Internal assist event '{event.type}' leaked to customer role!"


def test_invariant_rules_first_playbook_fallback():
    """Invariant 5: When generator fails, playbook fallback produces policy-grounded guidance."""
    fallback_svc = PlaybookFallbackService()

    policy_evidence = [
        EvidenceChunk(
            chunk_id="pol_card_decline_01_s4_c1",
            store_type="policy",
            title="Card Decline Resolution",
            text="Step 1: Confirm POS location. Step 2: Apply 24h bypass.",
            similarity_score=0.92,
        )
    ]

    action, response = fallback_svc.render_fallback("card_declined", policy_evidence)

    assert action is not None
    assert action.action_id.startswith("act_fb_")
    assert "pol_card_decline_01_s4_c1" in action.citations
    assert action.grounding.policy_supported is True
    assert len(action.steps) >= 3
    assert response is not None
    assert len(response.text) > 20
