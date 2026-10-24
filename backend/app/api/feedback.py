"""Agent Feedback REST API Router (Phase P9.8).

Receives human-in-the-loop agent feedback (thumbs up/down, intent corrections, disposition tracking)
and persists to database while streaming telemetry to BigQuery.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Literal

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.telemetry import get_telemetry_manager, trace_span
from app.db.base import get_session_factory
from app.db.models import FeedbackEventModel

logger = logging.getLogger("app.api.feedback")

router = APIRouter(prefix="/v1/feedback", tags=["feedback"])


class AgentFeedbackRequest(BaseModel):
    """Schema for agent assist feedback submission."""

    session_id: str = Field(..., description="Active session ID")
    item_type: Literal["recommendation", "response", "intent"] = Field(
        ..., description="Type of assist item being evaluated"
    )
    item_id: str = Field(..., description="Unique ID of the evaluated recommendation or response")
    agent_disposition: Literal["accepted", "edited", "dismissed"] = Field(
        ..., description="Disposition decision taken by the human agent"
    )
    rating: int | None = Field(
        default=None, description="Optional rating: 1 for thumbs up, -1 for thumbs down"
    )
    intent_correction: str | None = Field(
        default=None, description="Correct canonical intent label if classifier was suboptimal"
    )
    edited_text: str | None = Field(
        default=None, description="Custom text used if agent modified the suggested response"
    )
    comment: str | None = Field(
        default=None, description="Optional qualitative commentary or agent feedback notes"
    )


class AgentFeedbackResponse(BaseModel):
    """Response payload acknowledging feedback ingestion."""

    status: str
    feedback_id: str
    session_id: str
    agent_disposition: str
    timestamp: str


@router.post(
    "",
    response_model=AgentFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Agent Feedback",
)
async def submit_feedback(payload: AgentFeedbackRequest) -> dict[str, Any]:
    """Capture agent rating, disposition, or intent correction and record telemetry."""
    with trace_span(
        "api.submit_feedback",
        attributes={
            "session.id": payload.session_id,
            "feedback.item_type": payload.item_type,
            "feedback.disposition": payload.agent_disposition,
        },
    ):
        settings = get_settings()
        telemetry = get_telemetry_manager()
        telemetry.track_feedback(payload.agent_disposition)

        feedback_id = f"fb_{payload.session_id}_{int(time.time_ns())}"
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Persist to database if live PostgreSQL is active
        if settings.APP_PROFILE != "test":
            try:
                session_factory = get_session_factory()
                async with session_factory() as session:
                    async with session.begin():
                        record = FeedbackEventModel(
                            session_id=payload.session_id,
                            item_type=payload.item_type,
                            item_id=payload.item_id,
                            agent_disposition=payload.agent_disposition,
                            edited_text=payload.edited_text,
                            comment=payload.comment
                            or (
                                f"Intent correction: {payload.intent_correction}"
                                if payload.intent_correction
                                else None
                            ),
                        )
                        session.add(record)
            except Exception as e:
                logger.warning("Could not persist feedback event to database: %s", e)

        logger.info(
            "Agent feedback recorded: session=%s, type=%s, disposition=%s, rating=%s",
            payload.session_id,
            payload.item_type,
            payload.agent_disposition,
            payload.rating,
        )

        return {
            "status": "success",
            "feedback_id": feedback_id,
            "session_id": payload.session_id,
            "agent_disposition": payload.agent_disposition,
            "timestamp": timestamp,
        }
