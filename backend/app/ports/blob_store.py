"""Port protocol for binary and object storage (GCS / local emulator)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class BlobStore(Protocol):
    """Protocol for object storage abstraction."""

    async def upload_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload byte data and return its resource URI."""
        ...

    async def download_bytes(self, key: str) -> bytes:
        """Download raw byte data for a given key."""
        ...

    async def exists(self, key: str) -> bool:
        """Check if an object exists."""
        ...
