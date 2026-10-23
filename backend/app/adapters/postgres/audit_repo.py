"""PostgreSQL repository for tamper-evident append-only audit logging (R16)."""

from __future__ import annotations

import datetime
import hashlib
import json
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditEventModel


class PostgresAuditRepository:
    """Append-only audit repository computing cryptographic SHA-256 hash chains across events."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_latest_hash(self, session_id: str | None = None) -> str | None:
        """Fetch the most recent event hash to chain the next entry."""
        stmt = select(AuditEventModel.event_hash).order_by(desc(AuditEventModel.id)).limit(1)
        if session_id:
            stmt = (
                select(AuditEventModel.event_hash)
                .where(AuditEventModel.session_id == session_id)
                .order_by(desc(AuditEventModel.id))
                .limit(1)
            )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def record_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        session_id: str | None = None,
    ) -> AuditEventModel:
        """Append an audit record with cryptographic hash chaining."""
        prev_hash = await self.get_latest_hash(session_id) or "0" * 64
        now = datetime.datetime.now(datetime.UTC)

        # Canonical representation for tamper-evident hashing
        canonical_payload = json.dumps(payload, sort_keys=True, default=str)
        hash_preimage = (
            f"{prev_hash}|{session_id}|{event_type}|{canonical_payload}|{now.isoformat()}"
        )
        event_hash = hashlib.sha256(hash_preimage.encode("utf-8")).hexdigest()

        event = AuditEventModel(
            session_id=session_id,
            event_type=event_type,
            payload=payload,
            prev_hash=prev_hash,
            event_hash=event_hash,
            created_at=now,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def list_events(
        self,
        session_id: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[AuditEventModel]:
        """Query audit log entries."""
        stmt = select(AuditEventModel)
        if session_id:
            stmt = stmt.where(AuditEventModel.session_id == session_id)
        if event_type:
            stmt = stmt.where(AuditEventModel.event_type == event_type)
        stmt = stmt.order_by(AuditEventModel.created_at.asc(), AuditEventModel.id.asc()).limit(
            limit
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
