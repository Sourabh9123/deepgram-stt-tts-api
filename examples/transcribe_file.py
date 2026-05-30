"""Example script for transcribing a local audio file."""

import asyncio
import sys
from pathlib import Path

from app.config.settings import get_settings
from app.services.deepgram_client import DeepgramClient
from app.services.stt_service import SpeechToTextService
from app.utils.logging import configure_logging


async def main(audio_file: Path) -> None:
    """Transcribe a local audio file and print the normalized result."""
    settings = get_settings()
    configure_logging(settings.log_level)
    client = DeepgramClient(settings)
    service = SpeechToTextService(settings, client)
    try:
        result = await service.transcribe_file(audio_file)
        print(result.model_dump_json(indent=2))
    finally:
        await client.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python examples/transcribe_file.py path/to/audio.wav")
    asyncio.run(main(Path(sys.argv[1])))
