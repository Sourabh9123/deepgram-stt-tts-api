"""Application-specific exceptions."""

from typing import Any


class AppError(Exception):
    """Base class for expected application errors."""


class ConfigurationError(AppError):
    """Raised when required application configuration is missing or invalid."""


class DeepgramError(AppError):
    """Raised when a Deepgram operation fails."""


class DeepgramAPIError(DeepgramError):
    """Raised when Deepgram returns a non-successful API response."""

    def __init__(self, message: str, *, status_code: int, details: Any | None = None) -> None:
        """Initialize the API error with HTTP status and optional response details."""
        super().__init__(message)
        self.status_code = status_code
        self.details = details
