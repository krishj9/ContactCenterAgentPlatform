"""Redis Pub/Sub adapter implementing EventBus port for multi-worker WebSocket event distribution."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class RedisEventBus:
    """Distributed event bus over Redis Pub/Sub channels with in-memory fallback."""

    def __init__(self, redis_url: str | None = None) -> None:
        settings = get_settings()
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis_client: Any | None = None
        self._memory_subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}

    async def _get_client(self) -> Any:
        if self._redis_client is None:
            try:
                import redis.asyncio as aioredis

                self._redis_client = aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
            except Exception as e:
                logger.warning(
                    "Could not initialize Redis client for EventBus (%s). Using in-memory fallback.",
                    e,
                )
        return self._redis_client

    async def publish(self, topic: str, event: dict[str, Any]) -> None:
        """Publish event to Redis topic and notify in-memory subscribers."""
        payload_str = json.dumps(event)
        client = await self._get_client()

        if client is not None:
            try:
                await client.publish(topic, payload_str)
            except Exception as e:
                logger.debug(
                    "Redis publish failed on topic %s (%s). Routing through local fallback.",
                    topic,
                    e,
                )

        # Notify local in-memory subscribers
        if topic in self._memory_subscribers:
            for q in list(self._memory_subscribers[topic]):
                await q.put(event)

    async def subscribe(self, topic: str) -> AsyncIterator[dict[str, Any]]:
        """Subscribe to Redis channel and yield streaming events."""
        client = await self._get_client()
        local_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        if topic not in self._memory_subscribers:
            self._memory_subscribers[topic] = []
        self._memory_subscribers[topic].append(local_queue)

        if client is not None:
            try:
                pubsub = client.pubsub()
                await pubsub.subscribe(topic)

                async def _reader() -> None:
                    try:
                        async for message in pubsub.listen():
                            if message["type"] == "message":
                                data = message["data"]
                                if isinstance(data, str):
                                    event = json.loads(data)
                                    await local_queue.put(event)
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        logger.debug("Redis pubsub listener error on %s: %s", topic, e)

                task = asyncio.create_task(_reader())
                try:
                    while True:
                        item = await local_queue.get()
                        yield item
                finally:
                    task.cancel()
                    await pubsub.unsubscribe(topic)
                    await pubsub.close()
                    if (
                        topic in self._memory_subscribers
                        and local_queue in self._memory_subscribers[topic]
                    ):
                        self._memory_subscribers[topic].remove(local_queue)
                return
            except Exception as e:
                logger.debug(
                    "Redis subscribe failed on topic %s (%s). Using local queue.", topic, e
                )

        # In-memory subscription fallback
        try:
            while True:
                item = await local_queue.get()
                yield item
        finally:
            if topic in self._memory_subscribers and local_queue in self._memory_subscribers[topic]:
                self._memory_subscribers[topic].remove(local_queue)

    async def close(self) -> None:
        """Close active Redis connections."""
        if self._redis_client is not None:
            try:
                await self._redis_client.close()
            except Exception:
                pass
            self._redis_client = None
