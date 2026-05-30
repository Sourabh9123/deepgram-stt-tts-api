"""Unit tests for the speech-to-text service."""

from pathlib import Path
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from app.config.settings import AppSettings
from app.services.deepgram_client import DeepgramClient
from app.services.stt_service import SpeechToTextService


def settings(tmp_path: Path) -> AppSettings:
    """Build test settings without reading environment variables."""
    return AppSettings(deepgram_api_key=SecretStr("test-key"), audio_output_dir=tmp_path)


@pytest.mark.anyio
async def test_transcribe_bytes_returns_normalized_result(tmp_path: Path) -> None:
    """Verify STT service normalizes Deepgram transcription payloads."""

    async def handler(request: httpx.Request) -> httpx.Response:
        """Return a fake Deepgram STT response."""
        assert request.headers["authorization"] == "Token test-key"
        assert request.url.params["model"] == "nova-3"
        payload: dict[str, Any] = {
            "metadata": {"request_id": "abc", "duration": 1.2, "channels": 1},
            "results": {"channels": [{"alternatives": [{"transcript": "hello", "confidence": 0.98}]}]},
        }
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        test_settings = settings(tmp_path)
        client = DeepgramClient(test_settings, http_client)
        service = SpeechToTextService(test_settings, client)
        result = await service.transcribe_bytes(b"audio", content_type="audio/wav")

    assert result.transcript == "hello"
    assert result.confidence == 0.98
    assert result.metadata.request_id == "abc"
