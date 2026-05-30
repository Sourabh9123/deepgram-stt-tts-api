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
