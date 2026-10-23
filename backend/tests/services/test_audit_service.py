"""Unit tests validating AuditService and cryptographic hash chaining."""

import hashlib
import json

import pytest

from app.adapters.postgres.audit_repo import PostgresAuditRepository
from app.db.models import AuditEventModel
from app.services.audit_service import AuditCategory, AuditService


class InMemoryAuditRepo(PostgresAuditRepository):
    """In-memory mock satisfying PostgresAuditRepository interface for offline unit testing."""

    def __init__(self) -> None:
        self.events: list[AuditEventModel] = []

    async def get_latest_hash(self, session_id: str | None = None) -> str | None:
        filtered = self.events
        if session_id:
            filtered = [e for e in self.events if e.session_id == session_id]
        if not filtered:
            return None
        return filtered[-1].event_hash

    async def record_event(
        self,
        event_type: str,
        payload: dict[str, object],
        session_id: str | None = None,
    ) -> AuditEventModel:
        prev_hash = await self.get_latest_hash(session_id) or "0" * 64
        import datetime

        now = datetime.datetime.now(datetime.UTC)
        canonical = json.dumps(payload, sort_keys=True, default=str)
        hash_preimage = f"{prev_hash}|{session_id}|{event_type}|{canonical}|{now.isoformat()}"
        event_hash = hashlib.sha256(hash_preimage.encode("utf-8")).hexdigest()

        event = AuditEventModel(
            id=len(self.events) + 1,
            session_id=session_id,
            event_type=event_type,
            payload=payload,
            prev_hash=prev_hash,
            event_hash=event_hash,
            created_at=now,
        )
        self.events.append(event)
        return event

    async def list_events(
        self,
        session_id: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[AuditEventModel]:
        res = self.events
        if session_id:
            res = [e for e in res if e.session_id == session_id]
        if event_type:
            res = [e for e in res if e.event_type == event_type]
        return res[:limit]


@pytest.mark.asyncio
async def test_audit_service_lifecycle_and_hash_chain() -> None:
    repo = InMemoryAuditRepo()
    service = AuditService(audit_repo=repo)

    # 1. Log Session Lifecycle
    e1 = await service.log_session_lifecycle(
        session_id="sess_01",
        action="join",
        participant_id="part_agent_1",
        role="agent",
    )
    assert e1.event_type == AuditCategory.SESSION_LIFECYCLE
    assert e1.prev_hash == "0" * 64  # First genesis hash
    assert len(e1.event_hash) == 64

    # 2. Log Transcript Segment
    e2 = await service.log_transcript_segment(
        session_id="sess_01",
        turn_id=1,
        speaker="customer",
        text_length=42,
        duration_ms=1200.0,
    )
    assert e2.event_type == AuditCategory.TRANSCRIPT_SEGMENT
    assert e2.prev_hash == e1.event_hash  # Hash chain linked!

    # 3. Log Intent Prediction
    e3 = await service.log_intent_prediction(
        session_id="sess_01",
        turn_id=1,
        intent_label="card_declined",
        confidence=0.95,
        is_out_of_scope=False,
        model_version="gemma-3-1b-lora-v1",
        taxonomy_version="tx-14",
    )
    assert e3.prev_hash == e2.event_hash

    # 4. Log Grounding Decision
    e4 = await service.log_grounding_decision(
        session_id="sess_01",
        turn_id=1,
        grounding_state="GROUNDED",
        cited_chunk_ids=["POL-CARD-DECLINE-01"],
        policy_supported=True,
    )
    assert e4.prev_hash == e3.event_hash

    # 5. Log Recommendation
    e5 = await service.log_recommendation(
        session_id="sess_01",
        turn_id=1,
        action_id="act_lift_hold",
        grounding_state="GROUNDED",
        source_chunk_ids=["POL-CARD-DECLINE-01"],
        model_version="gemma-3-1b-lora-v1",
        prompt_version="prompt-nba-v1",
    )
    assert e5.prev_hash == e4.event_hash

    # 6. Log Agent Disposition
    e6 = await service.log_agent_disposition(
        session_id="sess_01",
        item_type="recommendation",
        item_id="act_lift_hold",
        disposition="accepted",
    )
    assert e6.prev_hash == e5.event_hash

    # 7. Log Summary Generation
    e7 = await service.log_summary_generation(
        session_id="sess_01",
        key_issues_count=1,
        actions_completed_count=2,
        model_version="gemma-3-1b-lora-v1",
    )
    assert e7.prev_hash == e6.event_hash

    # Verify event counts
    events = await repo.list_events(session_id="sess_01")
    assert len(events) == 7
