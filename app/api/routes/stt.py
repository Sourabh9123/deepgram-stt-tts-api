"""Speech-to-text routes."""

import base64
import binascii

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status

from app.api.deps import get_stt_service
from app.schemas.stt import Base64AudioRequest, STTResult
from app.services.stt_service import SpeechToTextService
from app.utils.exceptions import AppError, DeepgramAPIError
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/stt", response_model=STTResult)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str | None = Query(default=None, description="Optional BCP-47 language code."),
    service: SpeechToTextService = Depends(get_stt_service),
) -> STTResult:
    """Transcribe an uploaded audio file with Deepgram Nova."""
    try:
        audio = await file.read()
        content_type = file.content_type or "application/octet-stream"
        return await service.transcribe_bytes(audio, content_type=content_type, language=language)
    except DeepgramAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.details) from exc
    except (AppError, ValueError) as exc:
        logger.exception("stt_endpoint_error")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/stt/binary", response_model=STTResult)
async def transcribe_binary_stream(
    request: Request,
    model: str | None = Query(default=None, description="Optional Deepgram Nova model id."),
    language: str | None = Query(default=None, description="Optional BCP-47 language code."),
    service: SpeechToTextService = Depends(get_stt_service),
) -> STTResult:
    """Transcribe raw binary audio sent directly in the request body."""
    try:
        audio = await request.body()
        content_type = request.headers.get("content-type", "application/octet-stream")
        return await service.transcribe_bytes(audio, content_type=content_type, model=model, language=language)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DeepgramAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.details) from exc
    except AppError as exc:
        logger.exception("stt_binary_endpoint_error")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/stt/recording", response_model=STTResult)
async def transcribe_browser_recording(
    request: Request,
    model: str | None = Query(default=None, description="Optional Deepgram Nova model id."),
    language: str | None = Query(default=None, description="Optional BCP-47 language code."),
    service: SpeechToTextService = Depends(get_stt_service),
) -> STTResult:
    """Transcribe audio captured by the browser MediaRecorder API."""
    try:
        audio = await request.body()
        content_type = request.headers.get("content-type", "audio/webm")
        return await service.transcribe_bytes(audio, content_type=content_type, model=model, language=language)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DeepgramAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.details) from exc
    except AppError as exc:
        logger.exception("stt_recording_endpoint_error")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/stt/base64", response_model=STTResult)
async def transcribe_base64_audio(
    request: Base64AudioRequest,
    service: SpeechToTextService = Depends(get_stt_service),
) -> STTResult:
    """Transcribe base64-encoded audio sent in a JSON request body."""
    try:
        audio, content_type = _decode_base64_audio(request)
        return await service.transcribe_bytes(audio, content_type=content_type, model=request.model, language=request.language)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DeepgramAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.details) from exc
    except AppError as exc:
        logger.exception("stt_base64_endpoint_error")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


def _decode_base64_audio(request: Base64AudioRequest) -> tuple[bytes, str]:
    """Decode raw base64 audio or a base64 data URL into bytes and content type."""
    content_type = request.content_type
    encoded_audio = request.audio_base64.strip()
    if encoded_audio.startswith("data:"):
        header, separator, payload = encoded_audio.partition(",")
        if not separator:
            raise ValueError("Base64 data URL is missing a comma separator")
        content_type = header.removeprefix("data:").split(";", maxsplit=1)[0] or content_type
        encoded_audio = payload
    try:
        audio = base64.b64decode(encoded_audio, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Audio payload is not valid base64") from exc
    if not audio:
        raise ValueError("Audio payload is empty")
    return audio, content_type
