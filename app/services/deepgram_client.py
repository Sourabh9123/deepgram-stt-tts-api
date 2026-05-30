"""Reusable HTTP client for Deepgram REST APIs."""

import json
import mimetypes
from pathlib import Path
from typing import Any

import httpx

from app.config.settings import AppSettings
from app.utils.exceptions import DeepgramAPIError, DeepgramError
from app.utils.logging import get_logger, log_extra

logger = get_logger(__name__)


class DeepgramClient:
    """Small Deepgram REST client used by speech services."""

    def __init__(self, settings: AppSettings, http_client: httpx.AsyncClient | None = None) -> None:
        """Initialize the client with settings and an optional injected HTTP client."""
        self._settings = settings
        self._owns_client = http_client is None
        timeout = httpx.Timeout(settings.request_timeout_seconds)
        self._client = http_client or httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        """Close the underlying HTTP client when owned by this instance."""
        if self._owns_client:
            await self._client.aclose()

    async def post_audio_file(self, endpoint: str, file_path: Path, params: dict[str, Any]) -> dict[str, Any]:
        """Post a local audio file to a Deepgram endpoint and return JSON."""
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        data = file_path.read_bytes()
        return await self.post_audio_bytes(endpoint, data, content_type, params)

    async def post_audio_bytes(
        self,
        endpoint: str,
        audio: bytes,
        content_type: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Post audio bytes to a Deepgram endpoint and return JSON."""
        response = await self._request(
            "POST",
            endpoint,
            params=params,
            content=audio,
            headers={"Content-Type": content_type},
        )
        return self._parse_json_response(response)

    async def post_json_for_bytes(
        self,
        endpoint: str,
        payload: dict[str, Any],
        params: dict[str, Any],
    ) -> tuple[bytes, str]:
        """Post a JSON payload and return binary response bytes plus content type."""
        response = await self._request(
            "POST",
            endpoint,
            params=params,
            json_payload=payload,
            headers={"Content-Type": "application/json"},
        )
        return response.content, response.headers.get("content-type", "audio/mpeg")

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any],
        headers: dict[str, str],
        content: bytes | None = None,
        json_payload: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Send an authenticated request to Deepgram and handle transport/API errors."""
        url = f"{self._settings.deepgram_base_url}/{endpoint.lstrip('/')}"
        request_headers = {
            "Authorization": f"Token {self._settings.deepgram_api_key.get_secret_value()}",
            **headers,
        }
        safe_headers = {key: value for key, value in request_headers.items() if key.lower() != "authorization"}
        logger.info(
            "deepgram_request",
            extra=log_extra(method=method, url=url, params=params, headers=safe_headers),
        )
        try:
            response = await self._client.request(
                method,
                url,
                params=params,
                headers=request_headers,
                content=content,
                json=json_payload,
            )
        except httpx.HTTPError as exc:
            logger.exception("deepgram_transport_error", extra=log_extra(url=url))
            raise DeepgramError("Unable to reach Deepgram") from exc
        logger.info(
            "deepgram_response",
            extra=log_extra(status_code=response.status_code, url=str(response.url)),
        )
        if response.is_error:
            details = self._response_details(response)
            logger.error(
                "deepgram_api_error",
                extra=log_extra(status_code=response.status_code, details=details),
            )
            raise DeepgramAPIError(
                "Deepgram API request failed",
                status_code=response.status_code,
                details=details,
            )
        return response

    @staticmethod
    def _parse_json_response(response: httpx.Response) -> dict[str, Any]:
        """Parse a Deepgram JSON response."""
        try:
            parsed = response.json()
        except json.JSONDecodeError as exc:
            raise DeepgramError("Deepgram returned invalid JSON") from exc
        if not isinstance(parsed, dict):
            raise DeepgramError("Deepgram returned an unexpected JSON payload")
        return parsed

    @staticmethod
    def _response_details(response: httpx.Response) -> Any:
        """Return JSON error details when available, otherwise return response text."""
        try:
            return response.json()
        except json.JSONDecodeError:
            return response.text
