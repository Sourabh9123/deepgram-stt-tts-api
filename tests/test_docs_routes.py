"""Unit tests for protected API docs authentication."""

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPBasicCredentials
from pydantic import SecretStr

from app.api.routes.docs import verify_docs_credentials
from app.config.settings import AppSettings


def settings() -> AppSettings:
    """Build test docs credentials without reading environment variables."""
    return AppSettings(
        deepgram_api_key=SecretStr("test-key"),
        docs_username="admin",
        docs_password=SecretStr("secret"),
    )


def test_docs_credentials_accept_valid_username_and_password() -> None:
    """Verify docs auth accepts matching credentials."""
    credentials = HTTPBasicCredentials(username="admin", password="secret")

    assert verify_docs_credentials(credentials, settings()) is None


def test_docs_credentials_reject_invalid_password() -> None:
    """Verify docs auth rejects invalid credentials."""
    credentials = HTTPBasicCredentials(username="admin", password="wrong")

    with pytest.raises(HTTPException) as exc_info:
        verify_docs_credentials(credentials, settings())

    assert exc_info.value.status_code == 401
    assert exc_info.value.headers == {"WWW-Authenticate": "Basic"}
