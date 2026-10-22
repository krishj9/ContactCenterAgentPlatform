"""Test adapter for BlobStore port."""

from __future__ import annotations


class TestBlobStore:
    """In-memory dictionary object store."""

    __test__ = False

    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}

    async def upload_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        self._objects[key] = data
        return f"memory://test-bucket/{key}"

    async def download_bytes(self, key: str) -> bytes:
        if key not in self._objects:
            raise FileNotFoundError(f"Blob not found: {key}")
        return self._objects[key]

    async def exists(self, key: str) -> bool:
        return key in self._objects
