"""FastAPI application exposing Deepgram STT and TTS endpoints."""

import base64
import binascii
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile, status

from app.config.settings import AppSettings, get_settings
from app.schemas.stt import Base64AudioRequest, STTResult
from app.schemas.tts import TTSRequest, TTSResult
from app.services.deepgram_client import DeepgramClient
from app.services.stt_service import SpeechToTextService
from app.services.tts_service import TextToSpeechService
from app.utils.exceptions import AppError, DeepgramAPIError
from app.utils.logging import configure_logging, get_logger, log_extra

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Create shared application services and validate configuration on startup."""
    settings = get_settings()
    configure_logging(settings.log_level)
    deepgram_client = DeepgramClient(settings)
    application.state.settings = settings
    application.state.deepgram_client = deepgram_client
    application.state.stt_service = SpeechToTextService(settings, deepgram_client)
    application.state.tts_service = TextToSpeechService(settings, deepgram_client)
    logger.info("application_started", extra=log_extra(deepgram_base_url=settings.deepgram_base_url))
    try:
        yield
    finally:
        await deepgram_client.close()
        logger.info("application_stopped")


app = FastAPI(
    title="Deepgram Backend",
    version="1.0.0",
    description="Production-ready Deepgram STT and TTS integration.",
    lifespan=lifespan,
)


def get_app_settings() -> AppSettings:
    """Return validated application settings for dependency injection."""
    return get_settings()


def get_stt_service() -> SpeechToTextService:
    """Return the shared speech-to-text service."""
    return app.state.stt_service


def get_tts_service() -> TextToSpeechService:
    """Return the shared text-to-speech service."""
    return app.state.tts_service


@app.get("/health")
async def health(settings: AppSettings = Depends(get_app_settings)) -> dict[str, str]:
    """Return a lightweight health check response."""
    return {"status": "ok", "stt_model": settings.default_stt_model, "tts_model": settings.default_tts_model}


@app.post("/stt", response_model=STTResult)
async def transcribe_audio(
    file: UploadFile = File(...),
    service: SpeechToTextService = Depends(get_stt_service),
) -> STTResult:
    """Transcribe an uploaded audio file with Deepgram Nova."""
    try:
        audio = await file.read()
        content_type = file.content_type or "application/octet-stream"
        return await service.transcribe_bytes(audio, content_type=content_type)
    except DeepgramAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.details) from exc
    except (AppError, ValueError) as exc:
        logger.exception("stt_endpoint_error")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@app.post("/stt/binary", response_model=STTResult)
async def transcribe_binary_stream(
    request: Request,
    model: str | None = Query(default=None, description="Optional Deepgram Nova model id."),
    service: SpeechToTextService = Depends(get_stt_service),
) -> STTResult:
    """Transcribe raw binary audio sent directly in the request body."""
    try:
        audio = await request.body()
        content_type = request.headers.get("content-type", "application/octet-stream")
        return await service.transcribe_bytes(audio, content_type=content_type, model=model)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DeepgramAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.details) from exc
    except AppError as exc:
        logger.exception("stt_binary_endpoint_error")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@app.post("/stt/base64", response_model=STTResult)
async def transcribe_base64_audio(
    request: Base64AudioRequest,
    service: SpeechToTextService = Depends(get_stt_service),
) -> STTResult:
    """Transcribe base64-encoded audio sent in a JSON request body."""
    try:
        audio, content_type = _decode_base64_audio(request)
        return await service.transcribe_bytes(audio, content_type=content_type, model=request.model)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DeepgramAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.details) from exc
    except AppError as exc:
        logger.exception("stt_base64_endpoint_error")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@app.post("/tts", response_model=TTSResult)
async def synthesize_speech(
    request: TTSRequest,
    service: TextToSpeechService = Depends(get_tts_service),
) -> TTSResult:
    """Generate an MP3 file from text with Deepgram Aura."""
    try:
        return await service.synthesize_to_file(
            request.text,
            voice_model=request.voice_model,
            filename=request.filename,
        )
    except DeepgramAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.details) from exc
    except (AppError, ValueError) as exc:
        logger.exception("tts_endpoint_error")
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
