"""FastAPI application factory and runtime setup."""

from contextlib import asynccontextmanager
from os import getenv
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import docs, health, stt, tts
from app.config.settings import get_settings
from app.services.deepgram_client import DeepgramClient
from app.services.stt_service import SpeechToTextService
from app.services.tts_service import TextToSpeechService
from app.utils.logging import configure_logging, get_logger, log_extra

logger = get_logger(__name__)
load_dotenv()


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
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

app.mount("/audio", StaticFiles(directory=getenv("AUDIO_OUTPUT_DIR", "generated_audio"), check_dir=False), name="audio")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(stt.router)
app.include_router(tts.router)
app.include_router(docs.router)
