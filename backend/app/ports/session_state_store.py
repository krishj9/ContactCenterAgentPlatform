"""Port protocol for real-time session state and turn buffer management."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SessionStateStore(Protocol):
    """Protocol for session turn window buffers and task concurrency locks."""

    async def get_turn_window(self, session_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get the recent rolling turn window for a session."""
        ...

    async def append_turn(self, session_id: str, turn: dict[str, Any]) -> None:
        """Append a completed turn to the session buffer."""
        ...

    async def acquire_lock(self, lock_key: str, ttl_seconds: int = 5) -> bool:
        """Acquire a distributed lock to prevent overlapping assist runs."""
        ...

    async def release_lock(self, lock_key: str) -> None:
        """Release an acquired lock."""
        ...
