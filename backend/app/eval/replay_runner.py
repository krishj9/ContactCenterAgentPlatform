"""Transcript Replay Runner (R17).

Feeds golden scenario transcripts into the orchestrator pipeline without live audio,
recording all emitted WebSocket events for deterministic regression validation.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from eval.schema import ScenarioFixture

from app.contracts.events_v1 import (
    AssistRecommendationEvent,
    CustomerContextPayload,
    EventRole,
    EvidenceItemPayload,
    GroundingStatus,
    GuardrailAlertEvent,
    GuardrailSeverity,
    IntentCandidatePayload,
    IssueUpdateEvent,
    NextBestActionPayload,
    ProvenancePayload,
    SessionReadyEvent,
    SuggestedResponsePayload,
    SummaryReadyEvent,
    TranscriptFinalEvent,
    WebSocketEvent,
)
from app.core.container import Container, get_container
from app.domain.evidence import EvidenceChunk


@dataclass
class ReplayResult:
    """Summary of a scenario replay run."""

    scenario_id: str
    turns_replayed: int
    events_emitted: list[WebSocketEvent] = field(default_factory=list)
    predicted_intents: list[str] = field(default_factory=list)
    grounding_states: list[GroundingStatus] = field(default_factory=list)
    duration_ms: float = 0.0

    @property
    def total_events(self) -> int:
        return len(self.events_emitted)


class TranscriptReplayRunner:
    """Replays golden scenario transcripts deterministically using configured port adapters."""

    def __init__(self, container: Container | None = None) -> None:
        self.container = container or get_container()

    async def replay_scenario(
        self,
        scenario: ScenarioFixture | str | Path,
        session_id: str | None = None,
    ) -> ReplayResult:
        """Execute a full scenario replay, emitting simulated WebSocket event stream."""
        start_time = time.perf_counter()

        # Load scenario fixture if path provided
        if isinstance(scenario, str | Path):
            with open(scenario, encoding="utf-8") as f:
                scenario = ScenarioFixture.model_validate(json.load(f))

        sid = session_id or f"sess_{scenario.scenario_id}"
        events: list[WebSocketEvent] = []
        predicted_intents: list[str] = []
        grounding_states: list[GroundingStatus] = []

        # 1. Emit session.ready with Customer Context
        customer_ctx = CustomerContextPayload(
            customer_id=scenario.customer_profile.customer_id,
            name=scenario.customer_profile.name,
            account_type=scenario.customer_profile.account_type,
            relationship_tier=scenario.customer_profile.relationship_tier,
            account_number_masked=scenario.customer_profile.account_number_masked,
            context_summary=scenario.customer_profile.context_summary,
            extra=scenario.customer_profile.extra,
        )
        session_ready = SessionReadyEvent(
            session_id=sid,
            participant_id="part_agent_1",
            role=EventRole.AGENT,
            status="connected",
            customer_context=customer_ctx,
        )
        events.append(session_ready)

        customer_turns: list[str] = []
        all_turns: list[dict[str, Any]] = []

        # 2. Iterate through turns
        for turn in scenario.turns:
            role = EventRole(turn.speaker.value)
            all_turns.append({"turn_id": turn.turn_id, "speaker": role.value, "text": turn.text})

            # Emit transcript.final event
            final_turn = TranscriptFinalEvent(
                session_id=sid,
                turn_id=turn.turn_id,
                speaker=role,
                text=turn.text,
                duration_ms=1200.0,
            )
            events.append(final_turn)

            if role == EventRole.CUSTOMER:
                customer_turns.append(turn.text)
                # Classify intent using last <= 3 customer turns
                intent_pred = await self.container.intent_classifier.classify(customer_turns[-3:])
                predicted_intents.append(intent_pred.intent_label)

                # Emit issue.update (fast path)
                issue_event = IssueUpdateEvent(
                    session_id=sid,
                    turn_id=turn.turn_id,
                    intent_label=intent_pred.intent_label,
                    confidence=intent_pred.confidence,
                    is_out_of_scope=intent_pred.is_out_of_scope,
                    candidates=[
                        IntentCandidatePayload(intent_label=c.intent_label, confidence=c.confidence)
                        for c in intent_pred.candidate_intents
                    ],
                    exemplar_ids=intent_pred.explanation_exemplar_ids,
                    provenance=ProvenancePayload(
                        model_version=intent_pred.model_version,
                        taxonomy_version=intent_pred.taxonomy_version,
                    ),
                )
                events.append(issue_event)

                # Knowledge path / Grounding decision
                if (
                    intent_pred.is_out_of_scope
                    or intent_pred.confidence < self.container.settings.INTENT_CONFIDENCE_THRESHOLD
                ):
                    # Guardrail alert for out of scope or low confidence
                    alert = GuardrailAlertEvent(
                        session_id=sid,
                        turn_id=turn.turn_id,
                        code="OUT_OF_SCOPE"
                        if intent_pred.is_out_of_scope
                        else "LOW_INTENT_CONFIDENCE",
                        message=f"Intent '{intent_pred.intent_label}' out of operational scope.",
                        severity=GuardrailSeverity.WARNING,
                    )
                    events.append(alert)
                    grounding_states.append(GroundingStatus.MISSING_EVIDENCE)
                else:
                    # Retrieve evidence chunks (mocking or query matching)
                    evidence_chunks = [
                        EvidenceChunk(
                            chunk_id=c_id,
                            store_type="policy",
                            title=f"Policy rule {c_id}",
                            text=f"Authoritative procedure regarding {intent_pred.intent_label}",
                            similarity_score=0.88,
                        )
                        for c_id in (turn.required_citations or ["POL-BASE-01"])
                    ]

                    action, response = await self.container.generator.generate_action(
                        intent=intent_pred,
                        evidence=evidence_chunks,
                        customer_context=customer_ctx.model_dump(),
                    )

                    g_status = GroundingStatus(action.grounding.state.value)
                    grounding_states.append(g_status)

                    rec_event = AssistRecommendationEvent(
                        session_id=sid,
                        turn_id=turn.turn_id,
                        recommendations=[
                            NextBestActionPayload(
                                action_id=action.action_id,
                                title=action.title,
                                description=action.description,
                                action_type=action.action_type.value,
                                steps=action.steps,
                                is_grounded=action.is_grounded,
                                grounding_state=g_status,
                                citations=action.citations,
                            )
                        ],
                        suggested_response=SuggestedResponsePayload(
                            response_id=response.response_id,
                            text=response.text,
                            rationale=response.rationale,
                            is_editable=response.is_editable,
                            grounding_state=g_status,
                            citations=response.citations,
                        ),
                        evidence=[
                            EvidenceItemPayload(
                                chunk_id=c.chunk_id,
                                store_type=c.store_type,  # type: ignore[arg-type]
                                title=c.title,
                                snippet=c.text,
                                similarity_score=c.similarity_score,
                            )
                            for c in evidence_chunks
                        ],
                        grounding_state=g_status,
                        provenance=ProvenancePayload(),
                    )
                    events.append(rec_event)

        # 3. Emit summary.ready after turns complete
        summary = await self.container.generator.generate_summary(sid, all_turns)
        summary_event = SummaryReadyEvent(
            session_id=sid,
            call_overview=summary.call_overview,
            key_issues=summary.key_issues,
            actions_completed=summary.actions_completed,
            required_followups=summary.required_followups,
            crm_case_note=summary.crm_case_note,
            provenance=ProvenancePayload(),
        )
        events.append(summary_event)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return ReplayResult(
            scenario_id=scenario.scenario_id,
            turns_replayed=len(scenario.turns),
            events_emitted=events,
            predicted_intents=predicted_intents,
            grounding_states=grounding_states,
            duration_ms=round(elapsed_ms, 2),
        )
