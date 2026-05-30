"""Text-to-speech routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_tts_service
from app.schemas.tts import TTSRequest, TTSResult
from app.services.tts_service import TextToSpeechService
from app.utils.exceptions import AppError, DeepgramAPIError
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/tts", response_model=TTSResult)
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
