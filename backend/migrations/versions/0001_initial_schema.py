"""Initial schema with pgvector extension and all 11 core tables.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-23 15:52:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. sessions
    op.create_table(
        "sessions",
        sa.Column("session_id", sa.String(64), primary_key=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("customer_id", sa.String(64), nullable=True),
        sa.Column("customer_metadata", JSONB(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_sessions_status", "sessions", ["status"])
    op.create_index("ix_sessions_customer_id", "sessions", ["customer_id"])

    # 3. participants
    op.create_table(
        "participants",
        sa.Column("participant_id", sa.String(64), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("sessions.session_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column(
            "connected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("disconnected_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_participants_session_id", "participants", ["session_id"])

    # 4. transcript_segments
    op.create_table(
        "transcript_segments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("sessions.session_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("turn_id", sa.Integer(), nullable=False),
        sa.Column("speaker", sa.String(32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("is_final", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("duration_ms", sa.Float(), server_default="0.0", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_transcript_segments_session_id", "transcript_segments", ["session_id"])
    op.create_index("ix_transcript_segments_turn_id", "transcript_segments", ["turn_id"])

    # 5. issue_predictions
    op.create_table(
        "issue_predictions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("sessions.session_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("turn_id", sa.Integer(), nullable=False),
        sa.Column("intent_label", sa.String(128), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("is_out_of_scope", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("candidates", JSONB(), nullable=True),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("taxonomy_version", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_issue_predictions_session_id", "issue_predictions", ["session_id"])
    op.create_index("ix_issue_predictions_intent_label", "issue_predictions", ["intent_label"])

    # 6. recommendations
    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("sessions.session_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("turn_id", sa.Integer(), nullable=False),
        sa.Column("action_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("grounding_state", sa.String(64), nullable=False),
        sa.Column("action_type", sa.String(64), server_default="next_best_action", nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("corpus_version", sa.String(64), nullable=False),
        sa.Column("prompt_version", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_recommendations_session_id", "recommendations", ["session_id"])

    # 7. recommendation_sources
    op.create_table(
        "recommendation_sources",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "recommendation_id",
            sa.Integer(),
            sa.ForeignKey("recommendations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_id", sa.String(128), nullable=False),
        sa.Column("store_type", sa.String(64), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
    )
    op.create_index(
        "ix_recommendation_sources_rec_id", "recommendation_sources", ["recommendation_id"]
    )

    # 8. response_suggestions
    op.create_table(
        "response_suggestions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("sessions.session_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("turn_id", sa.Integer(), nullable=False),
        sa.Column("response_id", sa.String(64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("is_editable", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("grounding_state", sa.String(64), nullable=False),
        sa.Column("citations", JSONB(), server_default="[]", nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_response_suggestions_session_id", "response_suggestions", ["session_id"])

    # 9. summaries
    op.create_table(
        "summaries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("sessions.session_id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("call_overview", sa.Text(), nullable=False),
        sa.Column("key_issues", JSONB(), server_default="[]", nullable=False),
        sa.Column("actions_completed", JSONB(), server_default="[]", nullable=False),
        sa.Column("required_followups", JSONB(), server_default="[]", nullable=False),
        sa.Column("crm_case_note", sa.Text(), nullable=True),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_summaries_session_id", "summaries", ["session_id"])

    # 10. audit_events
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("sessions.session_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column("prev_hash", sa.String(64), nullable=True),
        sa.Column("event_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_audit_events_session_id", "audit_events", ["session_id"])
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"])

    # 11. feedback_events
    op.create_table(
        "feedback_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("sessions.session_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_type", sa.String(32), nullable=False),
        sa.Column("item_id", sa.String(64), nullable=False),
        sa.Column("agent_disposition", sa.String(32), nullable=False),
        sa.Column("edited_text", sa.Text(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_feedback_events_session_id", "feedback_events", ["session_id"])

    # 12. kb_chunks with pgvector (768) and tsvector
    op.create_table(
        "kb_chunks",
        sa.Column("chunk_id", sa.String(128), primary_key=True),
        sa.Column("store_type", sa.String(64), nullable=False),
        sa.Column("intent_label", sa.String(128), nullable=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("metadata_json", JSONB(), nullable=True),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column("tsv", TSVECTOR, nullable=True),
        sa.Column("status", sa.String(32), server_default="active", nullable=False),
        sa.Column("version_tag", sa.String(64), server_default="v1", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_kb_chunks_store_type", "kb_chunks", ["store_type"])
    op.create_index("ix_kb_chunks_intent_label", "kb_chunks", ["intent_label"])
    op.create_index("ix_kb_chunks_status", "kb_chunks", ["status"])

    # Gin index for full-text tsvector
    op.create_index("ix_kb_chunks_tsv", "kb_chunks", ["tsv"], postgresql_using="gin")

    # HNSW index for pgvector cosine distance
    op.create_index(
        "ix_kb_chunks_embedding",
        "kb_chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_table("kb_chunks")
    op.drop_table("feedback_events")
    op.drop_table("audit_events")
    op.drop_table("summaries")
    op.drop_table("response_suggestions")
    op.drop_table("recommendation_sources")
    op.drop_table("recommendations")
    op.drop_table("issue_predictions")
    op.drop_table("transcript_segments")
    op.drop_table("participants")
    op.drop_table("sessions")
    op.execute("DROP EXTENSION IF EXISTS vector;")
