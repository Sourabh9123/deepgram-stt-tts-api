"""Endpoint tests for speech-to-text request formats."""

from typing import Any

import pytest
from fastapi import HTTPException, Request

from app.api.routes.stt import transcribe_base64_audio, transcribe_binary_stream, transcribe_browser_recording
from app.schemas.stt import Base64AudioRequest, STTMetadata, STTResult


class FakeSpeechToTextService:
    """Fake STT service used to validate endpoint request handling."""

    def __init__(self) -> None:
        """Initialize the fake service with a call log."""
        self.calls: list[dict[str, Any]] = []

    async def transcribe_bytes(
        self,
        audio: bytes,
        *,
        content_type: str,
        model: str | None = None,
        language: str | None = None,
    ) -> STTResult:
        """Record the transcription call and return a static result."""
        self.calls.append({"audio": audio, "content_type": content_type, "model": model, "language": language})
        return STTResult(
            transcript="hello",
            confidence=0.99,
            metadata=STTMetadata(request_id="test", model=model or "nova-3"),
        )


def make_request(body: bytes, content_type: str) -> Request:
    """Create a minimal ASGI request with a fixed body."""
    sent = False

    async def receive() -> dict[str, Any]:
        """Return the request body once, then signal the end of the body."""
        nonlocal sent
        if sent:
            return {"type": "http.request", "body": b"", "more_body": False}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/stt/binary",
        "headers": [(b"content-type", content_type.encode("ascii"))],
        "query_string": b"",
    }
    return Request(scope, receive)  # type: ignore[arg-type]


@pytest.mark.anyio
async def test_binary_stt_endpoint_accepts_raw_audio() -> None:
    """Verify the binary endpoint forwards raw request body audio."""
    service = FakeSpeechToTextService()
    request = make_request(b"audio-bytes", "audio/wav")

    result = await transcribe_binary_stream(request, "nova-3", "hi", service)  # type: ignore[arg-type]

    assert result.transcript == "hello"
    assert service.calls == [{"audio": b"audio-bytes", "content_type": "audio/wav", "model": "nova-3", "language": "hi"}]


@pytest.mark.anyio
async def test_recording_stt_endpoint_accepts_browser_audio() -> None:
    """Verify the recording endpoint forwards browser-captured audio."""
    service = FakeSpeechToTextService()
    request = make_request(b"webm-bytes", "audio/webm")

    result = await transcribe_browser_recording(request, "nova-3", "es", service)  # type: ignore[arg-type]

    assert result.transcript == "hello"
    assert service.calls == [{"audio": b"webm-bytes", "content_type": "audio/webm", "model": "nova-3", "language": "es"}]


@pytest.mark.anyio
async def test_base64_stt_endpoint_accepts_json_audio() -> None:
    """Verify the base64 endpoint decodes JSON audio before transcription."""
    service = FakeSpeechToTextService()
    request = Base64AudioRequest(audio_base64="YXVkaW8tYnl0ZXM=", content_type="audio/mpeg", language="fr")

    result = await transcribe_base64_audio(request, service)  # type: ignore[arg-type]

    assert result.confidence == 0.99
    assert service.calls == [{"audio": b"audio-bytes", "content_type": "audio/mpeg", "model": None, "language": "fr"}]


@pytest.mark.anyio
async def test_base64_stt_endpoint_accepts_data_url() -> None:
    """Verify the base64 endpoint understands browser-style data URLs."""
    service = FakeSpeechToTextService()
    request = Base64AudioRequest(audio_base64="data:audio/webm;base64,YXVkaW8tYnl0ZXM=")

    await transcribe_base64_audio(request, service)  # type: ignore[arg-type]

    assert service.calls == [{"audio": b"audio-bytes", "content_type": "audio/webm", "model": None, "language": None}]


@pytest.mark.anyio
async def test_base64_stt_endpoint_rejects_invalid_audio() -> None:
    """Verify invalid base64 payloads return a client error."""
    service = FakeSpeechToTextService()
    request = Base64AudioRequest(audio_base64="not valid base64")

    with pytest.raises(HTTPException) as exc_info:
        await transcribe_base64_audio(request, service)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 400
    assert service.calls == []
