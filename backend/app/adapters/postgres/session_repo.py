"""PostgreSQL repository for Sessions and Participants."""

from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ParticipantModel, SessionModel


class PostgresSessionRepository:
    """Async repository managing session lifecycle and participant connections in PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_session(
        self,
        session_id: str,
        customer_id: str | None = None,
        customer_metadata: dict[str, Any] | None = None,
    ) -> SessionModel:
        """Create and persist a new session."""
        db_session = SessionModel(
            session_id=session_id,
            status="active",
            customer_id=customer_id,
            customer_metadata=customer_metadata,
        )
        self.session.add(db_session)
        await self.session.flush()
        return db_session

    async def get_session(self, session_id: str) -> SessionModel | None:
        """Fetch session by ID."""
        stmt = select(SessionModel).where(SessionModel.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(self, session_id: str, status: str) -> SessionModel | None:
        """Update session status (e.g. ended, active)."""
        db_session = await self.get_session(session_id)
        if db_session:
            db_session.status = status
            await self.session.flush()
        return db_session

    async def add_participant(
        self,
        session_id: str,
        participant_id: str,
        role: str,
    ) -> ParticipantModel:
        """Register a participant connection."""
        participant = ParticipantModel(
            session_id=session_id,
            participant_id=participant_id,
            role=role,
        )
        self.session.add(participant)
        await self.session.flush()
        return participant

    async def disconnect_participant(self, participant_id: str) -> ParticipantModel | None:
        """Record participant disconnection timestamp."""
        stmt = select(ParticipantModel).where(ParticipantModel.participant_id == participant_id)
        result = await self.session.execute(stmt)
        participant = result.scalar_one_or_none()
        if participant:
            participant.disconnected_at = datetime.datetime.now(datetime.UTC)
            await self.session.flush()
        return participant

    async def list_participants(self, session_id: str) -> list[ParticipantModel]:
        """List all participants for a session."""
        stmt = (
            select(ParticipantModel)
            .where(ParticipantModel.session_id == session_id)
            .order_by(ParticipantModel.connected_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
