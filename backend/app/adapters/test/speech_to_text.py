"""Test adapter for SpeechToText port."""

from __future__ import annotations

from collections.abc import AsyncIterator


class TestSpeechToText:
    """Deterministic in-memory speech-to-text adapter."""

    __test__ = False

    def __init__(
        self, canned_transcript: str = "I am calling about my debit card being declined."
    ) -> None:
        self.canned_transcript = canned_transcript

    async def transcribe_stream(
        self,
        audio_chunks: AsyncIterator[bytes],
        session_id: str,
        participant_id: str,
    ) -> AsyncIterator[tuple[str, bool]]:
        """Yield partial then final transcript for testing streaming handlers."""
        words = self.canned_transcript.split()
        partial = ""
        for i, word in enumerate(words):
            partial += f"{word} "
            is_final = i == len(words) - 1
            yield (partial.strip(), is_final)

    async def transcribe_chunk(self, chunk: bytes, is_final: bool = False) -> str:
        """Return canned transcript."""
        return self.canned_transcript
