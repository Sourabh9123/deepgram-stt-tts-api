"""Unit tests for the text-to-speech service."""

from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

from app.config.settings import AppSettings
from app.services.deepgram_client import DeepgramClient
from app.services.tts_service import TextToSpeechService


def settings(tmp_path: Path) -> AppSettings:
    """Build test settings without reading environment variables."""
    return AppSettings(deepgram_api_key=SecretStr("test-key"), audio_output_dir=tmp_path)


@pytest.mark.anyio
async def test_synthesize_to_file_writes_mp3(tmp_path: Path) -> None:
    """Verify TTS service writes Deepgram audio bytes to disk."""

    async def handler(request: httpx.Request) -> httpx.Response:
        """Return fake Deepgram audio bytes."""
        assert request.headers["authorization"] == "Token test-key"
        assert request.url.params["model"] == "aura-2-thalia-en"
        return httpx.Response(200, content=b"mp3-bytes", headers={"content-type": "audio/mpeg"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        test_settings = settings(tmp_path)
        client = DeepgramClient(test_settings, http_client)
        service = TextToSpeechService(test_settings, client)
        result = await service.synthesize_to_file("Hello", filename="hello")

    assert result.file_path.read_bytes() == b"mp3-bytes"
    assert result.file_path.name == "hello.mp3"
    assert result.bytes_written == 9
