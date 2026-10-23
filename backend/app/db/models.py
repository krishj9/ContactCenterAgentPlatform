"""SQLAlchemy 2.0 ORM models for Contact Center Agent Helper platform.

Tables:
- sessions
- participants
- transcript_segments
- issue_predictions
- recommendations
- recommendation_sources
- response_suggestions
- summaries
- audit_events
- feedback_events
- kb_chunks (with pgvector vector(768) and tsvector columns)
"""

from __future__ import annotations

import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base

# Universal JSON type using JSONB on PostgreSQL and JSON elsewhere
JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")


class SessionModel(Base):
    """Voice/chat contact center session."""

    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False, index=True)
    customer_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    customer_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON_TYPE, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    participants: Mapped[list[ParticipantModel]] = relationship(
        "ParticipantModel", back_populates="session", cascade="all, delete-orphan"
    )
    transcripts: Mapped[list[TranscriptSegmentModel]] = relationship(
        "TranscriptSegmentModel", back_populates="session", cascade="all, delete-orphan"
    )
    issue_predictions: Mapped[list[IssuePredictionModel]] = relationship(
        "IssuePredictionModel", back_populates="session", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list[RecommendationModel]] = relationship(
        "RecommendationModel", back_populates="session", cascade="all, delete-orphan"
    )
    response_suggestions: Mapped[list[ResponseSuggestionModel]] = relationship(
        "ResponseSuggestionModel", back_populates="session", cascade="all, delete-orphan"
    )
    summary: Mapped[SummaryModel | None] = relationship(
        "SummaryModel", back_populates="session", uselist=False, cascade="all, delete-orphan"
    )
    audit_events: Mapped[list[AuditEventModel]] = relationship(
        "AuditEventModel", back_populates="session", cascade="all, delete-orphan"
    )
    feedback_events: Mapped[list[FeedbackEventModel]] = relationship(
        "FeedbackEventModel", back_populates="session", cascade="all, delete-orphan"
    )


class ParticipantModel(Base):
    """Session participant (agent or customer)."""

    __tablename__ = "participants"

    participant_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # agent | customer
    connected_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    disconnected_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    session: Mapped[SessionModel] = relationship("SessionModel", back_populates="participants")


class TranscriptSegmentModel(Base):
    """Spoken or text transcript turn segment."""

    __tablename__ = "transcript_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    turn_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    speaker: Mapped[str] = mapped_column(String(32), nullable=False)  # agent | customer | system
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_final: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[SessionModel] = relationship("SessionModel", back_populates="transcripts")


class IssuePredictionModel(Base):
    """Intent prediction and confidence classification for a turn."""

    __tablename__ = "issue_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    turn_id: Mapped[int] = mapped_column(Integer, nullable=False)
    intent_label: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    is_out_of_scope: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    candidates: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON_TYPE, nullable=True)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    taxonomy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[SessionModel] = relationship("SessionModel", back_populates="issue_predictions")


class RecommendationModel(Base):
    """Grounded Next-Best-Action recommendation."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    turn_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    grounding_state: Mapped[str] = mapped_column(String(64), nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), default="next_best_action", nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    corpus_version: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[SessionModel] = relationship("SessionModel", back_populates="recommendations")
    sources: Mapped[list[RecommendationSourceModel]] = relationship(
        "RecommendationSourceModel", back_populates="recommendation", cascade="all, delete-orphan"
    )


class RecommendationSourceModel(Base):
    """Cited policy chunks backing a recommendation."""

    __tablename__ = "recommendation_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recommendation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_id: Mapped[str] = mapped_column(String(128), nullable=False)
    store_type: Mapped[str] = mapped_column(String(64), nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)

    recommendation: Mapped[RecommendationModel] = relationship(
        "RecommendationModel", back_populates="sources"
    )


class ResponseSuggestionModel(Base):
    """Editable suggested response for the human agent."""

    __tablename__ = "response_suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    turn_id: Mapped[int] = mapped_column(Integer, nullable=False)
    response_id: Mapped[str] = mapped_column(String(64), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    is_editable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    grounding_state: Mapped[str] = mapped_column(String(64), nullable=False)
    citations: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[SessionModel] = relationship(
        "SessionModel", back_populates="response_suggestions"
    )


class SummaryModel(Base):
    """Post-call conversation disposition and notes."""

    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    call_overview: Mapped[str] = mapped_column(Text, nullable=False)
    key_issues: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    actions_completed: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    required_followups: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    crm_case_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[SessionModel] = relationship("SessionModel", back_populates="summary")


class AuditEventModel(Base):
    """Append-only audit event log (R16) with tamper-evident hash chaining."""

    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("sessions.session_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False)
    prev_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    session: Mapped[SessionModel | None] = relationship(
        "SessionModel", back_populates="audit_events"
    )


class FeedbackEventModel(Base):
    """Human-in-the-loop agent feedback on assist recommendations."""

    __tablename__ = "feedback_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_type: Mapped[str] = mapped_column(String(32), nullable=False)  # recommendation | response
    item_id: Mapped[str] = mapped_column(String(64), nullable=False)
    agent_disposition: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # accepted | edited | dismissed
    edited_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[SessionModel] = relationship("SessionModel", back_populates="feedback_events")


class KBChunkModel(Base):
    """Knowledge base chunk with dense pgvector embedding and sparse full-text tsvector."""

    __tablename__ = "kb_chunks"

    chunk_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    store_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    intent_label: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON_TYPE, nullable=True)
    embedding = mapped_column(Vector(768), nullable=True)
    tsv = mapped_column(TSVECTOR, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False, index=True)
    version_tag: Mapped[str] = mapped_column(String(64), default="v1", nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_kb_chunks_tsv", "tsv", postgresql_using="gin"),
        Index(
            "ix_kb_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
