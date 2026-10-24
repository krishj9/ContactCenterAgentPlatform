"""Role-based outbound event fanout filter ensuring customer isolation (R9, R14)."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Events strictly prohibited from ever reaching customer WebSocket connections
INTERNAL_ASSIST_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "issue.update",
        "assist.recommendation",
        "guardrail.alert",
        "summary.ready",
        "recommendation.update",
        "response_suggestion.update",
        "guardrail.warning",
    }
)

# Events allowed for customer sockets
CUSTOMER_ALLOWED_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "session.ready",
        "transcript.partial",
        "transcript.final",
        "session.end",
    }
)


class OutboundEventFilter:
    """Filters outgoing events before transmission over WebSocket connections based on participant role."""

    @staticmethod
    def is_event_allowed_for_role(event_type: str, role: str) -> bool:
        """Return True if event_type is permitted for participant role."""
        normalized_role = (role or "").strip().lower()
        if normalized_role == "customer":
            return (
                event_type in CUSTOMER_ALLOWED_EVENT_TYPES
                and event_type not in INTERNAL_ASSIST_EVENT_TYPES
            )
        # Agents and system roles receive all operational events
        return True

    @classmethod
    def filter_event_for_role(
        cls,
        event: dict[str, Any] | BaseModel,
        role: str,
    ) -> dict[str, Any] | None:
        """Filter and sanitize event payload for the specified role. Returns None if suppressed."""
        payload: dict[str, Any] = (
            event.model_dump(mode="json") if isinstance(event, BaseModel) else dict(event)
        )
        event_type = payload.get("type", "")

        if not cls.is_event_allowed_for_role(event_type, role):
            logger.debug(
                "Suppressed internal event '%s' from routing to '%s' participant",
                event_type,
                role,
            )
            return None

        # Sanitize sensitive fields if streaming session.ready to customer
        if (role or "").strip().lower() == "customer" and event_type == "session.ready":
            customer_context = payload.get("customer_context")
            if isinstance(customer_context, dict) and "extra" in customer_context:
                # Remove internal scoring/extra metadata from customer-visible context
                sanitized_context = dict(customer_context)
                sanitized_context.pop("extra", None)
                payload["customer_context"] = sanitized_context

        return payload
