"""Test adapter for EventBus port."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any


class TestEventBus:
    """In-memory event bus with asyncio Queue subscribers."""

    __test__ = False

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}
        self.published_events: list[tuple[str, dict[str, Any]]] = []

    async def publish(self, topic: str, event: dict[str, Any]) -> None:
        self.published_events.append((topic, event))
        if topic in self._subscribers:
            for q in self._subscribers[topic]:
                await q.put(event)

    async def subscribe(self, topic: str) -> AsyncIterator[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(q)

        try:
            while True:
                item = await q.get()
                yield item
        finally:
            self._subscribers[topic].remove(q)
