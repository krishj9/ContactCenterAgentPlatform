"""Port protocol for distributed pub/sub event distribution."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class EventBus(Protocol):
    """Protocol for cross-instance WebSocket event distribution."""

    async def publish(self, topic: str, event: dict[str, Any]) -> None:
        """Publish an event payload to a topic/channel."""
        ...

    def subscribe(self, topic: str) -> AsyncIterator[dict[str, Any]]:
        """Subscribe to a topic and yield stream of event payloads."""
        ...
