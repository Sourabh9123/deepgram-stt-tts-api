"""Speech-to-text request and response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class STTMetadata(BaseModel):
    """Metadata returned from a Deepgram transcription request."""

    request_id: str | None = None
    model: str
    duration: float | None = None
    channels: int | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class STTResult(BaseModel):
    """Normalized speech-to-text result returned by the application."""

    transcript: str
    confidence: float
    metadata: STTMetadata


class Base64AudioRequest(BaseModel):
    """Request body for base64-encoded audio transcription."""

    audio_base64: str = Field(min_length=1, description="Raw base64 audio or a data URL.")
    content_type: str = Field(default="application/octet-stream", description="Audio MIME type.")
    model: str | None = Field(default=None, description="Optional Deepgram Nova model id.")
