"""Text-to-speech request and response schemas."""

from pathlib import Path

from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    """Request body for text-to-speech generation."""

    text: str = Field(min_length=1, max_length=4_000)
    voice_model: str | None = Field(default=None, description="Deepgram Aura model id.")
    filename: str | None = Field(default=None, description="Optional output filename.")


class TTSResult(BaseModel):
    """Normalized text-to-speech result returned by the application."""

    file_path: Path
    voice_model: str
    bytes_written: int
    content_type: str
