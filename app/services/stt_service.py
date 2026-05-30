"""Speech-to-text service backed by Deepgram Nova."""

from pathlib import Path
from typing import Any

from app.config.settings import AppSettings
from app.schemas.stt import STTMetadata, STTResult
from app.services.deepgram_client import DeepgramClient
from app.utils.exceptions import DeepgramError
from app.utils.logging import get_logger, log_extra

logger = get_logger(__name__)


class SpeechToTextService:
    """Transcribe audio with Deepgram's prerecorded speech-to-text API."""

    def __init__(self, settings: AppSettings, client: DeepgramClient) -> None:
        """Initialize the service with validated settings and a Deepgram client."""
        self._settings = settings
        self._client = client

    async def transcribe_file(self, file_path: Path, model: str | None = None) -> STTResult:
        """Transcribe a local audio file and return a normalized result."""
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        logger.info("stt_file_received", extra=log_extra(file_path=str(file_path), bytes=file_path.stat().st_size))
        payload = await self._client.post_audio_file("listen", file_path, self._stt_params(model))
        return self._to_result(payload, model or self._settings.default_stt_model)

    async def transcribe_bytes(
        self,
        audio: bytes,
        *,
        content_type: str,
        model: str | None = None,
    ) -> STTResult:
        """Transcribe in-memory audio bytes and return a normalized result."""
        if not audio:
            raise ValueError("Audio payload is empty")
        logger.info("stt_bytes_received", extra=log_extra(bytes=len(audio), content_type=content_type))
        payload = await self._client.post_audio_bytes("listen", audio, content_type, self._stt_params(model))
        return self._to_result(payload, model or self._settings.default_stt_model)

    def _stt_params(self, model: str | None) -> dict[str, Any]:
        """Build Deepgram STT query parameters."""
        return {
            "model": model or self._settings.default_stt_model,
            "smart_format": "true",
        }

    @staticmethod
    def _to_result(payload: dict[str, Any], model: str) -> STTResult:
        """Convert a Deepgram transcription response into the public result schema."""
        try:
            channel = payload["results"]["channels"][0]
            alternative = channel["alternatives"][0]
            transcript = str(alternative.get("transcript", ""))
            confidence = float(alternative.get("confidence", 0.0) or 0.0)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise DeepgramError("Deepgram transcription response had an unexpected shape") from exc
        metadata_payload = payload.get("metadata", {})
        metadata = STTMetadata(
            request_id=metadata_payload.get("request_id"),
            model=model,
            duration=metadata_payload.get("duration"),
            channels=metadata_payload.get("channels"),
            raw=metadata_payload,
        )
        logger.info(
            "stt_completed",
            extra=log_extra(confidence=confidence, transcript_length=len(transcript), request_id=metadata.request_id),
        )
        return STTResult(transcript=transcript, confidence=confidence, metadata=metadata)
