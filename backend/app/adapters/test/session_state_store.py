"""Test adapter for SessionStateStore port."""

from __future__ import annotations

from typing import Any


class TestSessionStateStore:
    """In-memory session state and lock store for offline testing."""

    __test__ = False

    def __init__(self) -> None:
        self._turns: dict[str, list[dict[str, Any]]] = {}
        self._locks: set[str] = set()

    async def get_turn_window(self, session_id: str, limit: int = 10) -> list[dict[str, Any]]:
        turns = self._turns.get(session_id, [])
        return turns[-limit:]

    async def append_turn(self, session_id: str, turn: dict[str, Any]) -> None:
        if session_id not in self._turns:
            self._turns[session_id] = []
        self._turns[session_id].append(turn)

    async def acquire_lock(self, lock_key: str, ttl_seconds: int = 5) -> bool:
        if lock_key in self._locks:
            return False
        self._locks.add(lock_key)
        return True

    async def release_lock(self, lock_key: str) -> None:
        self._locks.discard(lock_key)
