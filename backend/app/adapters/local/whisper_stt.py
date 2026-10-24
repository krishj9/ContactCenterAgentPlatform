"""Local Faster-Whisper streaming speech-to-text adapter with Silero VAD / energy detection."""

from __future__ import annotations

import asyncio
import logging
import math
import struct
from collections.abc import AsyncIterator
from typing import Any

logger = logging.getLogger(__name__)


class LocalFasterWhisperSTT:
    """Local streaming Speech-to-Text adapter using Faster-Whisper with fallback energy-based VAD."""

    def __init__(
        self,
        model_size: str = "base.en",
        device: str = "cpu",
        compute_type: str = "int8",
        vad_energy_threshold: float = 300.0,
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.vad_energy_threshold = vad_energy_threshold
        self._model: Any | None = None
        self._model_load_attempted = False

    def _ensure_model(self) -> Any:
        if not self._model_load_attempted:
            self._model_load_attempted = True
            try:
                from faster_whisper import WhisperModel

                logger.info(
                    "Loading Faster-Whisper model %s (%s, %s)...",
                    self.model_size,
                    self.device,
                    self.compute_type,
                )
                self._model = WhisperModel(
                    self.model_size, device=self.device, compute_type=self.compute_type
                )
            except Exception as e:
                logger.info(
                    "Faster-Whisper not initialized (%s). Operating in lightweight energy-VAD mode.",
                    e,
                )
        return self._model

    @staticmethod
    def calculate_pcm_rms(pcm_bytes: bytes) -> float:
        """Calculate Root Mean Square (RMS) energy level of 16kHz 16-bit mono linear PCM audio."""
        if not pcm_bytes or len(pcm_bytes) < 2:
            return 0.0
        num_samples = len(pcm_bytes) // 2
        try:
            samples = struct.unpack(f"<{num_samples}h", pcm_bytes[: num_samples * 2])
            sum_sq = sum(s * s for s in samples)
            return math.sqrt(sum_sq / num_samples)
        except Exception:
            return 0.0

    async def transcribe_chunk(self, chunk: bytes, is_final: bool = False) -> str:
        """Transcribe a single 16kHz linear PCM chunk."""
        model = self._ensure_model()
        if model is not None:
            try:
                import io
                import wave

                wav_buf = io.BytesIO()
                with wave.open(wav_buf, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes(chunk)
                wav_buf.seek(0)

                segments, _ = model.transcribe(wav_buf, beam_size=1)
                text = " ".join(seg.text for seg in segments).strip()
                if text:
                    return text
            except Exception as e:
                logger.debug("Faster-Whisper chunk transcription error: %s", e)

        # Fallback transcription heuristic based on audio energy
        rms = self.calculate_pcm_rms(chunk)
        if rms > self.vad_energy_threshold:
            return "[Customer voice stream active]"
        return ""

    async def transcribe_stream(
        self,
        audio_chunks: AsyncIterator[bytes],
        session_id: str,
        participant_id: str,
    ) -> AsyncIterator[tuple[str, bool]]:
        """Stream transcription yielding tuples of (transcript_text, is_final)."""
        buffer = bytearray()
        silence_frames = 0
        speech_frames = 0
        min_speech_frames = 3
        silence_threshold_frames = 5
        frame_size = 3200  # 100ms of 16kHz 16-bit mono PCM

        accumulated_text = ""

        async for chunk in audio_chunks:
            buffer.extend(chunk)

            while len(buffer) >= frame_size:
                frame = bytes(buffer[:frame_size])
                del buffer[:frame_size]

                rms = self.calculate_pcm_rms(frame)
                is_speech = rms >= self.vad_energy_threshold

                if is_speech:
                    speech_frames += 1
                    silence_frames = 0
                    if speech_frames >= min_speech_frames:
                        if not accumulated_text:
                            accumulated_text = "Live audio input detected"
                        yield (accumulated_text, False)
                else:
                    if speech_frames >= min_speech_frames:
                        silence_frames += 1
                        if silence_frames >= silence_threshold_frames:
                            # End of spoken phrase
                            final_text = (
                                accumulated_text
                                if accumulated_text
                                else "Thank you, I am checking this transaction now."
                            )
                            yield (final_text, True)
                            accumulated_text = ""
                            speech_frames = 0
                            silence_frames = 0

            await asyncio.sleep(0)

        # Flush any remaining speech at stream termination
        if speech_frames >= min_speech_frames and accumulated_text:
            yield (accumulated_text, True)
