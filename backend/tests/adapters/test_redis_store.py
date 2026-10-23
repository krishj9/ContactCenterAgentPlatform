"""Unit tests validating RedisSessionStore logic offline."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.adapters.redis.state_store import RedisSessionStore


class MockRedisPipeline:
    """Mock async redis pipeline."""

    def __init__(self, storage: dict[str, list[str]]) -> None:
        self.storage = storage
        self.commands: list[tuple[str, str, str]] = []

    def rpush(self, key: str, value: str) -> None:
        self.commands.append(("rpush", key, value))

    def expire(self, key: str, ttl: int) -> None:
        self.commands.append(("expire", key, str(ttl)))

    async def execute(self) -> None:
        for cmd, key, val in self.commands:
            if cmd == "rpush":
                self.storage.setdefault(key, []).append(val)
        self.commands.clear()

    async def __aenter__(self) -> "MockRedisPipeline":
        return self

    async def __aexit__(self, *args: object) -> None:
        pass


@pytest.mark.asyncio
async def test_redis_session_store_turn_window_and_locks() -> None:
    store = RedisSessionStore.__new__(RedisSessionStore)
    mock_redis = AsyncMock()
    store._redis = mock_redis

    storage: dict[str, list[str]] = {}
    mock_redis.pipeline = MagicMock(return_value=MockRedisPipeline(storage))

    # 1. Append turns
    await store.append_turn(
        "sess_01", {"turn_id": 1, "speaker": "customer", "text": "Card declined"}
    )
    await store.append_turn("sess_01", {"turn_id": 2, "speaker": "agent", "text": "I can help"})

    assert len(storage["session:sess_01:turns"]) == 2

    # 2. Get turn window
    mock_redis.lrange.return_value = storage["session:sess_01:turns"]
    window = await store.get_turn_window("sess_01", limit=10)
    assert len(window) == 2
    assert window[0]["text"] == "Card declined"
    assert window[1]["text"] == "I can help"

    # 3. Test distributed locks
    mock_redis.set.return_value = True
    acquired = await store.acquire_lock("turn_lock_1", ttl_seconds=5)
    assert acquired is True
    mock_redis.set.assert_called_with("lock:turn_lock_1", "locked", nx=True, ex=5)

    # 4. Release lock
    await store.release_lock("turn_lock_1")
    mock_redis.delete.assert_called_with("lock:turn_lock_1")

    # 5. Message deduplication
    mock_redis.set.return_value = True
    is_dup1 = await store.is_message_duplicate("msg_101", ttl_seconds=60)
    assert is_dup1 is False

    mock_redis.set.return_value = None  # Key exists, set fails
    is_dup2 = await store.is_message_duplicate("msg_101", ttl_seconds=60)
    assert is_dup2 is True
