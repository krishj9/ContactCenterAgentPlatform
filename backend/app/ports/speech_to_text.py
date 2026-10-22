"""Port protocol for streaming speech-to-text engines."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable


@runtime_checkable
class SpeechToText(Protocol):
    """Protocol for streaming speech transcription engines."""

    def transcribe_stream(
        self,
        audio_chunks: AsyncIterator[bytes],
        session_id: str,
        participant_id: str,
    ) -> AsyncIterator[tuple[str, bool]]:
        """Stream transcription yielding tuples of (transcript_text, is_final)."""
        ...

    async def transcribe_chunk(self, chunk: bytes, is_final: bool = False) -> str:
        """Transcribe a single 16kHz PCM audio chunk synchronously or offline."""
        ...
