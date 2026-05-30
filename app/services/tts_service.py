"""Text-to-speech service backed by Deepgram Aura."""

from pathlib import Path
from uuid import uuid4

from app.config.settings import AppSettings
from app.schemas.tts import TTSResult
from app.services.deepgram_client import DeepgramClient
from app.utils.logging import get_logger, log_extra

logger = get_logger(__name__)


class TextToSpeechService:
    """Generate speech audio with Deepgram's text-to-speech API."""

    def __init__(self, settings: AppSettings, client: DeepgramClient) -> None:
        """Initialize the service with validated settings and a Deepgram client."""
        self._settings = settings
        self._client = client

    async def synthesize_to_file(
        self,
        text: str,
        *,
        voice_model: str | None = None,
        filename: str | None = None,
    ) -> TTSResult:
        """Convert text to speech and save the generated MP3 file."""
        cleaned_text = text.strip()
        if not cleaned_text:
            raise ValueError("Text must not be empty")
        selected_model = voice_model or self._settings.default_tts_model
        output_path = self._build_output_path(filename)
        logger.info(
            "tts_request_received",
            extra=log_extra(text_length=len(cleaned_text), voice_model=selected_model, output_path=str(output_path)),
        )
        audio, content_type = await self._client.post_json_for_bytes(
            "speak",
            {"text": cleaned_text},
            {"model": selected_model},
        )
        output_path.write_bytes(audio)
        logger.info(
            "tts_completed",
            extra=log_extra(bytes_written=len(audio), voice_model=selected_model, output_path=str(output_path)),
        )
        return TTSResult(
            file_path=output_path,
            audio_url=f"/audio/{output_path.name}",
            voice_model=selected_model,
            bytes_written=len(audio),
            content_type=content_type,
        )

    def _build_output_path(self, filename: str | None) -> Path:
        """Build a safe MP3 output path inside the configured output directory."""
        safe_name = Path(filename).name if filename else f"{uuid4().hex}.mp3"
        if not safe_name.lower().endswith(".mp3"):
            safe_name = f"{safe_name}.mp3"
        return self._settings.audio_output_dir / safe_name
