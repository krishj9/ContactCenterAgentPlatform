"""Audit Service (R16) persisting tamper-evident audit events to PostgreSQL."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.postgres.audit_repo import PostgresAuditRepository
from app.db.models import AuditEventModel


class AuditCategory(StrEnum):
    """Standardized R16 audit event categories."""

    SESSION_LIFECYCLE = "SESSION_LIFECYCLE"
    TRANSCRIPT_SEGMENT = "TRANSCRIPT_SEGMENT"
    INTENT_PREDICTION = "INTENT_PREDICTION"
    RETRIEVAL_CALL = "RETRIEVAL_CALL"
    GROUNDING_DECISION = "GROUNDING_DECISION"
    RECOMMENDATION = "RECOMMENDATION"
    AGENT_DISPOSITION = "AGENT_DISPOSITION"
    SUMMARY_GENERATION = "SUMMARY_GENERATION"
    GUARDRAIL_ALERT = "GUARDRAIL_ALERT"


class AuditService:
    """Service providing strongly-typed audit persistence with SHA-256 tamper-evident hash chaining."""

    def __init__(
        self, audit_repo: PostgresAuditRepository | None = None, session: AsyncSession | None = None
    ) -> None:
        if audit_repo is not None:
            self.audit_repo = audit_repo
        elif session is not None:
            self.audit_repo = PostgresAuditRepository(session)
        else:
            raise ValueError("Either audit_repo or session must be provided to AuditService")

    async def log_session_lifecycle(
        self,
        session_id: str,
        action: str,  # join | disconnect | end
        participant_id: str,
        role: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEventModel:
        """Record session lifecycle transition."""
        payload = {
            "action": action,
            "participant_id": participant_id,
            "role": role,
            "metadata": metadata or {},
        }
        return await self.audit_repo.record_event(
            event_type=AuditCategory.SESSION_LIFECYCLE,
            payload=payload,
            session_id=session_id,
        )

    async def log_transcript_segment(
        self,
        session_id: str,
        turn_id: int,
        speaker: str,
        text_length: int,
        duration_ms: float,
    ) -> AuditEventModel:
        """Record transcript turn segment."""
        payload = {
            "turn_id": turn_id,
            "speaker": speaker,
            "text_length": text_length,
            "duration_ms": duration_ms,
        }
        return await self.audit_repo.record_event(
            event_type=AuditCategory.TRANSCRIPT_SEGMENT,
            payload=payload,
            session_id=session_id,
        )

    async def log_intent_prediction(
        self,
        session_id: str,
        turn_id: int,
        intent_label: str,
        confidence: float,
        is_out_of_scope: bool,
        model_version: str,
        taxonomy_version: str,
    ) -> AuditEventModel:
        """Record intent classification event."""
        payload = {
            "turn_id": turn_id,
            "intent_label": intent_label,
            "confidence": confidence,
            "is_out_of_scope": is_out_of_scope,
            "model_version": model_version,
            "taxonomy_version": taxonomy_version,
        }
        return await self.audit_repo.record_event(
            event_type=AuditCategory.INTENT_PREDICTION,
            payload=payload,
            session_id=session_id,
        )

    async def log_retrieval_call(
        self,
        session_id: str,
        turn_id: int,
        store_type: str,
        retrieved_chunk_ids: list[str],
        top_similarity_score: float,
    ) -> AuditEventModel:
        """Record knowledge retrieval invocation."""
        payload = {
            "turn_id": turn_id,
            "store_type": store_type,
            "retrieved_chunk_ids": retrieved_chunk_ids,
            "top_similarity_score": top_similarity_score,
        }
        return await self.audit_repo.record_event(
            event_type=AuditCategory.RETRIEVAL_CALL,
            payload=payload,
            session_id=session_id,
        )

    async def log_grounding_decision(
        self,
        session_id: str,
        turn_id: int,
        grounding_state: str,
        cited_chunk_ids: list[str],
        policy_supported: bool,
    ) -> AuditEventModel:
        """Record grounding evaluation decision (R10, R13)."""
        payload = {
            "turn_id": turn_id,
            "grounding_state": grounding_state,
            "cited_chunk_ids": cited_chunk_ids,
            "policy_supported": policy_supported,
        }
        return await self.audit_repo.record_event(
            event_type=AuditCategory.GROUNDING_DECISION,
            payload=payload,
            session_id=session_id,
        )

    async def log_recommendation(
        self,
        session_id: str,
        turn_id: int,
        action_id: str,
        grounding_state: str,
        source_chunk_ids: list[str],
        model_version: str,
        prompt_version: str,
    ) -> AuditEventModel:
        """Record assist recommendation generation."""
        payload = {
            "turn_id": turn_id,
            "action_id": action_id,
            "grounding_state": grounding_state,
            "source_chunk_ids": source_chunk_ids,
            "model_version": model_version,
            "prompt_version": prompt_version,
        }
        return await self.audit_repo.record_event(
            event_type=AuditCategory.RECOMMENDATION,
            payload=payload,
            session_id=session_id,
        )

    async def log_agent_disposition(
        self,
        session_id: str,
        item_type: str,
        item_id: str,
        disposition: str,  # accepted | edited | dismissed
        edited_text: str | None = None,
    ) -> AuditEventModel:
        """Record human agent action on suggestion."""
        payload = {
            "item_type": item_type,
            "item_id": item_id,
            "disposition": disposition,
            "has_edits": edited_text is not None,
        }
        return await self.audit_repo.record_event(
            event_type=AuditCategory.AGENT_DISPOSITION,
            payload=payload,
            session_id=session_id,
        )

    async def log_guardrail_alert(
        self,
        session_id: str,
        turn_id: int,
        code: str,
        severity: str,
        message: str,
    ) -> AuditEventModel:
        """Record safety guardrail alert."""
        payload = {
            "turn_id": turn_id,
            "code": code,
            "severity": severity,
            "message": message,
        }
        return await self.audit_repo.record_event(
            event_type=AuditCategory.GUARDRAIL_ALERT,
            payload=payload,
            session_id=session_id,
        )

    async def log_summary_generation(
        self,
        session_id: str,
        key_issues_count: int,
        actions_completed_count: int,
        model_version: str,
    ) -> AuditEventModel:
        """Record summary generation."""
        payload = {
            "key_issues_count": key_issues_count,
            "actions_completed_count": actions_completed_count,
            "model_version": model_version,
        }
        return await self.audit_repo.record_event(
            event_type=AuditCategory.SUMMARY_GENERATION,
            payload=payload,
            session_id=session_id,
        )
