"""PostgreSQL repository for assist recommendations, predictions, and summaries."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    FeedbackEventModel,
    IssuePredictionModel,
    RecommendationModel,
    RecommendationSourceModel,
    ResponseSuggestionModel,
    SummaryModel,
)


class PostgresRecommendationRepository:
    """Async repository persisting assist outputs and human agent dispositions in PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_issue_prediction(
        self,
        session_id: str,
        turn_id: int,
        intent_label: str,
        confidence: float,
        is_out_of_scope: bool,
        model_version: str,
        taxonomy_version: str,
        candidates: list[dict[str, Any]] | None = None,
    ) -> IssuePredictionModel:
        """Persist intent classification outcome."""
        prediction = IssuePredictionModel(
            session_id=session_id,
            turn_id=turn_id,
            intent_label=intent_label,
            confidence=confidence,
            is_out_of_scope=is_out_of_scope,
            candidates=candidates,
            model_version=model_version,
            taxonomy_version=taxonomy_version,
        )
        self.session.add(prediction)
        await self.session.flush()
        return prediction

    async def save_recommendation(
        self,
        session_id: str,
        turn_id: int,
        action_id: str,
        title: str,
        description: str,
        grounding_state: str,
        model_version: str,
        corpus_version: str,
        prompt_version: str,
        sources: list[dict[str, Any]],
        action_type: str = "next_best_action",
    ) -> RecommendationModel:
        """Persist next-best-action recommendation along with citation sources."""
        rec = RecommendationModel(
            session_id=session_id,
            turn_id=turn_id,
            action_id=action_id,
            title=title,
            description=description,
            grounding_state=grounding_state,
            action_type=action_type,
            model_version=model_version,
            corpus_version=corpus_version,
            prompt_version=prompt_version,
        )
        self.session.add(rec)
        await self.session.flush()

        for s in sources:
            source = RecommendationSourceModel(
                recommendation_id=rec.id,
                chunk_id=s["chunk_id"],
                store_type=s["store_type"],
                similarity_score=s["similarity_score"],
                title=s["title"],
            )
            self.session.add(source)

        await self.session.flush()
        return rec

    async def save_response_suggestion(
        self,
        session_id: str,
        turn_id: int,
        response_id: str,
        text: str,
        rationale: str,
        grounding_state: str,
        citations: list[str],
        model_version: str,
        is_editable: bool = True,
    ) -> ResponseSuggestionModel:
        """Persist suggested response."""
        suggestion = ResponseSuggestionModel(
            session_id=session_id,
            turn_id=turn_id,
            response_id=response_id,
            text=text,
            rationale=rationale,
            grounding_state=grounding_state,
            citations=citations,
            model_version=model_version,
            is_editable=is_editable,
        )
        self.session.add(suggestion)
        await self.session.flush()
        return suggestion

    async def save_summary(
        self,
        session_id: str,
        call_overview: str,
        key_issues: list[str],
        actions_completed: list[str],
        required_followups: list[str],
        model_version: str,
        crm_case_note: str | None = None,
    ) -> SummaryModel:
        """Persist post-call disposition summary."""
        summary = SummaryModel(
            session_id=session_id,
            call_overview=call_overview,
            key_issues=key_issues,
            actions_completed=actions_completed,
            required_followups=required_followups,
            crm_case_note=crm_case_note,
            model_version=model_version,
        )
        self.session.add(summary)
        await self.session.flush()
        return summary

    async def record_feedback(
        self,
        session_id: str,
        item_type: str,
        item_id: str,
        agent_disposition: str,
        edited_text: str | None = None,
        comment: str | None = None,
    ) -> FeedbackEventModel:
        """Record human-in-the-loop agent disposition (accepted/edited/dismissed)."""
        feedback = FeedbackEventModel(
            session_id=session_id,
            item_type=item_type,
            item_id=item_id,
            agent_disposition=agent_disposition,
            edited_text=edited_text,
            comment=comment,
        )
        self.session.add(feedback)
        await self.session.flush()
        return feedback

    async def get_latest_recommendation(self, session_id: str) -> RecommendationModel | None:
        """Fetch latest recommendation for a session with citations preloaded."""
        stmt = (
            select(RecommendationModel)
            .where(RecommendationModel.session_id == session_id)
            .options(selectinload(RecommendationModel.sources))
            .order_by(RecommendationModel.turn_id.desc(), RecommendationModel.id.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
