"""PostgreSQL repository for conversation transcript segments."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TranscriptSegmentModel


class PostgresTranscriptRepository:
    """Async repository persisting spoken and text transcript turns in PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_segment(
        self,
        session_id: str,
        turn_id: int,
        speaker: str,
        text: str,
        is_final: bool = True,
        duration_ms: float = 0.0,
    ) -> TranscriptSegmentModel:
        """Persist a transcript turn segment."""
        segment = TranscriptSegmentModel(
            session_id=session_id,
            turn_id=turn_id,
            speaker=speaker,
            text=text,
            is_final=is_final,
            duration_ms=duration_ms,
        )
        self.session.add(segment)
        await self.session.flush()
        return segment

    async def get_segments(
        self,
        session_id: str,
        only_final: bool = True,
    ) -> list[TranscriptSegmentModel]:
        """Fetch all transcript segments for a session ordered by turn_id."""
        stmt = select(TranscriptSegmentModel).where(TranscriptSegmentModel.session_id == session_id)
        if only_final:
            stmt = stmt.where(TranscriptSegmentModel.is_final.is_(True))
        stmt = stmt.order_by(TranscriptSegmentModel.turn_id, TranscriptSegmentModel.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
