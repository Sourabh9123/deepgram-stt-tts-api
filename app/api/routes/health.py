"""Health check routes."""

from fastapi import APIRouter, Depends

from app.api.deps import get_app_settings
from app.config.settings import AppSettings

router = APIRouter()


@router.get("/health")
async def health(settings: AppSettings = Depends(get_app_settings)) -> dict[str, str]:
    """Return a lightweight health check response."""
    return {"status": "ok", "stt_model": settings.default_stt_model, "tts_model": settings.default_tts_model}
