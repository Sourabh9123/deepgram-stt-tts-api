"""Shared FastAPI dependencies."""

from fastapi import Request

from app.config.settings import AppSettings
from app.services.stt_service import SpeechToTextService
from app.services.tts_service import TextToSpeechService


def get_app_settings(request: Request) -> AppSettings:
    """Return validated application settings from app state."""
    return request.app.state.settings


def get_stt_service(request: Request) -> SpeechToTextService:
    """Return the shared speech-to-text service."""
    return request.app.state.stt_service


def get_tts_service(request: Request) -> TextToSpeechService:
    """Return the shared text-to-speech service."""
    return request.app.state.tts_service
