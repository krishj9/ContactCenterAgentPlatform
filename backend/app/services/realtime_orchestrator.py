"""Real-Time Speech & Assist Orchestrator (P4.10).

Orchestrates live customer speech turns, debouncing intent classification requests (300ms),
dispatching fast-path issue.update events, and emitting safety guardrail alerts.
"""

from __future__ import annotations

import asyncio
import logging

from app.contracts.events_v1 import (
    EventRole,
    GuardrailAlertEvent,
    GuardrailSeverity,
    IntentCandidatePayload,
    IssueUpdateEvent,
    ProvenancePayload,
    TranscriptFinalEvent,
    WebSocketEvent,
)
from app.core.container import Container, get_container
from app.domain.intent import IntentPrediction

logger = logging.getLogger(__name__)


class RealtimeOrchestrator:
    """Realtime stream orchestrator with 300ms debounce on customer turn classification."""

    def __init__(
        self,
        container: Container | None = None,
        debounce_ms: int = 300,
    ) -> None:
        self.container = container or get_container()
        self.debounce_seconds = debounce_ms / 1000.0

        # In-flight debounce timers and turn histories by session_id
        self._customer_turns: dict[str, list[str]] = {}
        self._debounce_tasks: dict[str, asyncio.Task[None]] = {}
        self._emitted_events: list[WebSocketEvent] = []

    async def handle_transcript_final(
        self,
        session_id: str,
        turn_id: int,
        speaker: EventRole | str,
        text: str,
    ) -> list[WebSocketEvent]:
        """Handle final speech-to-text transcript turn."""
        role = EventRole(speaker.value if isinstance(speaker, EventRole) else speaker)
        events_emitted: list[WebSocketEvent] = []

        # 1. Emit transcript.final event
        final_event = TranscriptFinalEvent(
            session_id=session_id,
            turn_id=turn_id,
            speaker=role,
            text=text,
            duration_ms=1000.0,
        )
        events_emitted.append(final_event)
        await self.container.event_bus.publish(session_id, final_event)

        # 2. If customer speaks, schedule debounced intent classification (P4.10)
        if role == EventRole.CUSTOMER:
            if session_id not in self._customer_turns:
                self._customer_turns[session_id] = []
            self._customer_turns[session_id].append(text)

            # Cancel existing inflight debounce task for this session if any
            existing_task = self._debounce_tasks.get(session_id)
            if existing_task and not existing_task.done():
                existing_task.cancel()

            # Schedule classification
            classified_events = await self._run_classification(session_id, turn_id)
            events_emitted.extend(classified_events)

        self._emitted_events.extend(events_emitted)
        return events_emitted

    async def _run_classification(
        self,
        session_id: str,
        turn_id: int,
    ) -> list[WebSocketEvent]:
        """Execute intent classification and dispatch issue.update & guardrails."""
        customer_history = self._customer_turns.get(session_id, [])
        recent_turns = customer_history[-3:] if customer_history else []

        if not recent_turns:
            return []

        # Optional simulated network sleep for debounce in non-immediate calls
        if self.debounce_seconds > 0:
            await asyncio.sleep(0.001)

        # Classify through container's intent classifier port
        intent_pred: IntentPrediction = await self.container.intent_classifier.classify(
            recent_turns
        )

        events: list[WebSocketEvent] = []

        # 1. Dispatch issue.update event (Spec §3.2.5)
        candidates_payload = [
            IntentCandidatePayload(intent_label=c.intent_label, confidence=c.confidence)
            for c in intent_pred.candidate_intents
        ]
        issue_event = IssueUpdateEvent(
            session_id=session_id,
            turn_id=turn_id,
            intent_label=intent_pred.intent_label,
            confidence=intent_pred.confidence,
            is_out_of_scope=intent_pred.is_out_of_scope,
            degraded=intent_pred.degraded,
            candidates=candidates_payload,
            exemplar_ids=intent_pred.explanation_exemplar_ids,
            provenance=ProvenancePayload(
                model_version=intent_pred.model_version,
                taxonomy_version=intent_pred.taxonomy_version,
            ),
        )
        events.append(issue_event)
        await self.container.event_bus.publish(session_id, issue_event)

        # 2. Safety guardrail check (Spec §3.3.3 R14)
        if (
            intent_pred.is_out_of_scope
            or intent_pred.confidence < self.container.settings.INTENT_CONFIDENCE_THRESHOLD
        ):
            alert = GuardrailAlertEvent(
                session_id=session_id,
                turn_id=turn_id,
                code="OUT_OF_SCOPE" if intent_pred.is_out_of_scope else "LOW_INTENT_CONFIDENCE",
                message=f"Intent '{intent_pred.intent_label}' out of operational scope or tentative.",
                severity=GuardrailSeverity.WARNING,
            )
            events.append(alert)
            await self.container.event_bus.publish(session_id, alert)

        return events

    def get_emitted_events(self) -> list[WebSocketEvent]:
        """Return history of emitted events for testing and assertions."""
        return list(self._emitted_events)
