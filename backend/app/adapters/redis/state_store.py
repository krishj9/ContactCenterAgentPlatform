"""Redis-backed session state store for rolling turn windows, distributed locks, and message deduplication."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis

from app.core.config import get_settings
from app.ports.session_state_store import SessionStateStore


class RedisSessionStore(SessionStateStore):
    """Session state store using Redis 7 for transient state management."""

    def __init__(self, redis_url: str | None = None) -> None:
        url = redis_url or get_settings().REDIS_URL
        self._redis: aioredis.Redis = aioredis.from_url(
            url,
            encoding="utf-8",
            decode_responses=True,
        )

    async def get_turn_window(self, session_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get the recent rolling turn window for a session from a Redis list."""
        key = f"session:{session_id}:turns"
        raw_items = await self._redis.lrange(key, -limit, -1)
        turns: list[dict[str, Any]] = []
        for item in raw_items:
            try:
                turns.append(json.loads(item))
            except json.JSONDecodeError:
                continue
        return turns

    async def append_turn(self, session_id: str, turn: dict[str, Any]) -> None:
        """Append a completed turn to the session list buffer and set 24h TTL."""
        key = f"session:{session_id}:turns"
        payload = json.dumps(turn)
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.rpush(key, payload)
            pipe.expire(key, 86400)  # 24 hour retention for active session buffer
            await pipe.execute()

    async def acquire_lock(self, lock_key: str, ttl_seconds: int = 5) -> bool:
        """Acquire a distributed lock using Redis SET NX EX to prevent concurrency races."""
        full_key = f"lock:{lock_key}"
        # SET key value NX EX ttl
        acquired = await self._redis.set(full_key, "locked", nx=True, ex=ttl_seconds)
        return bool(acquired)

    async def release_lock(self, lock_key: str) -> None:
        """Release an acquired lock."""
        full_key = f"lock:{lock_key}"
        await self._redis.delete(full_key)

    async def is_message_duplicate(self, message_id: str, ttl_seconds: int = 60) -> bool:
        """Return True if message has already been processed/published recently, False otherwise."""
        dedupe_key = f"dedupe:{message_id}"
        # Attempt to set key; if it already exists, set returns None -> duplicate
        acquired = await self._redis.set(dedupe_key, "1", nx=True, ex=ttl_seconds)
        return not bool(acquired)

    async def clear_session(self, session_id: str) -> None:
        """Delete all transient keys associated with a session."""
        keys = await self._redis.keys(f"session:{session_id}:*")
        if keys:
            await self._redis.delete(*keys)

    async def close(self) -> None:
        """Close connection pool."""
        await self._redis.aclose()
