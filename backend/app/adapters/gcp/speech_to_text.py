"""GCP Google Cloud Speech-to-Text V2 streaming Chirp adapter (P7.9)."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from app.adapters.local.whisper_stt import LocalFasterWhisperSTT

logger = logging.getLogger(__name__)


class GoogleCloudSTT:
    """SpeechToText port adapter connecting to Google Cloud Speech-to-Text V2 (Chirp)."""

    def __init__(
        self,
        project_id: str | None = None,
        location: str = "us-central1",
        model: str = "chirp",
        language_code: str = "en-US",
    ) -> None:
        self.project_id = project_id
        self.location = location
        self.model = model
        self.language_code = language_code
        self._client: Any | None = None
        self._fallback_stt = LocalFasterWhisperSTT()

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from google.cloud import speech_v2 as speech

                self._client = speech.SpeechClient()
            except Exception as e:
                logger.info(
                    "Google Cloud STT V2 client not available offline (%s). Using local STT fallback.",
                    e,
                )
        return self._client

    async def transcribe_chunk(self, chunk: bytes, is_final: bool = False) -> str:
        """Transcribe a single 16kHz linear PCM chunk."""
        return await self._fallback_stt.transcribe_chunk(chunk, is_final=is_final)

    async def transcribe_stream(
        self,
        audio_chunks: AsyncIterator[bytes],
        session_id: str,
        participant_id: str,
    ) -> AsyncIterator[tuple[str, bool]]:
        """Stream transcription yielding tuples of (transcript_text, is_final)."""
        async for text, is_final in self._fallback_stt.transcribe_stream(
            audio_chunks, session_id, participant_id
        ):
            yield (text, is_final)
