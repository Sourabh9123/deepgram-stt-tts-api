"""Application settings loaded from environment variables."""

from functools import lru_cache
from os import getenv
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr, ValidationError, field_validator

from app.utils.exceptions import ConfigurationError


class AppSettings(BaseModel):
    """Validated runtime settings for the application."""

    deepgram_api_key: SecretStr = Field(min_length=1)
    deepgram_base_url: str = "https://api.deepgram.com/v1"
    default_stt_model: str = "nova-3"
    default_stt_language: str = "en"
    default_tts_model: str = "aura-2-thalia-en"
    audio_output_dir: Path = Path("generated_audio")
    request_timeout_seconds: float = Field(default=60.0, gt=0)
    log_level: str = "INFO"
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    docs_username: str = "admin"
    docs_password: SecretStr = SecretStr("change-me")

    @field_validator("deepgram_base_url")
    @classmethod
    def normalize_base_url(cls, value: str) -> str:
        """Normalize the Deepgram base URL to avoid double slashes in requests."""
        return value.rstrip("/")

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        """Normalize log level names for the standard logging module."""
        return value.upper()


def _env_value(name: str, default: str | None = None) -> str | None:
    """Read an environment variable and treat empty strings as missing values."""
    value = getenv(name, default)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Load, validate, and cache application settings."""
    load_dotenv()
    raw_settings: dict[str, Any] = {
        "deepgram_api_key": _env_value("DEEPGRAM_API_KEY"),
        "deepgram_base_url": _env_value("DEEPGRAM_BASE_URL", "https://api.deepgram.com/v1"),
        "default_stt_model": _env_value("DEFAULT_STT_MODEL", "nova-3"),
        "default_stt_language": _env_value("DEFAULT_STT_LANGUAGE", "en"),
        "default_tts_model": _env_value("DEFAULT_TTS_MODEL", "aura-2-thalia-en"),
        "audio_output_dir": Path(_env_value("AUDIO_OUTPUT_DIR", "generated_audio") or "generated_audio"),
        "request_timeout_seconds": float(_env_value("REQUEST_TIMEOUT_SECONDS", "60") or "60"),
        "log_level": _env_value("LOG_LEVEL", "INFO"),
        "cors_allowed_origins": [
            origin.strip() for origin in (_env_value("CORS_ALLOWED_ORIGINS", "http://localhost:5173") or "").split(",") if origin.strip()
        ],
        "docs_username": _env_value("DOCS_USERNAME", "admin"),
        "docs_password": SecretStr(_env_value("DOCS_PASSWORD", "change-me") or "change-me"),
    }
    try:
        settings = AppSettings(**raw_settings)
    except ValidationError as exc:
        raise ConfigurationError("Invalid application configuration") from exc
    settings.audio_output_dir.mkdir(parents=True, exist_ok=True)
    return settings
