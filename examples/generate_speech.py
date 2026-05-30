"""Example script for generating MP3 speech from text."""

import asyncio
import sys

from app.config.settings import get_settings
from app.services.deepgram_client import DeepgramClient
from app.services.tts_service import TextToSpeechService
from app.utils.logging import configure_logging


async def main(text: str) -> None:
    """Generate speech from text and print the saved file path."""
    settings = get_settings()
    configure_logging(settings.log_level)
    client = DeepgramClient(settings)
    service = TextToSpeechService(settings, client)
    try:
        result = await service.synthesize_to_file(text)
        print(result.model_dump_json(indent=2))
    finally:
        await client.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python examples/generate_speech.py "Hello from Deepgram"')
    asyncio.run(main(" ".join(sys.argv[1:])))
