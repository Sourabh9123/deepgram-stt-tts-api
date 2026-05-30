# Deepgram Python Backend

Production-ready Python 3.12+ backend integration for Deepgram Speech-to-Text and Text-to-Speech.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Set `DEEPGRAM_API_KEY` in `.env`.

## Run FastAPI

```bash
uvicorn app.main:app --reload
```

## Docker

```bash
docker compose up --build
```

## Example Usage

```bash
python examples/transcribe_file.py ./sample.wav
python examples/generate_speech.py "Hello from Deepgram"
```

## API

```bash
curl -X POST http://localhost:8000/stt \
  -F "file=@sample.wav"

curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello from Deepgram","voice_model":"aura-2-thalia-en"}'
```

## Tests

```bash
pytest
```
