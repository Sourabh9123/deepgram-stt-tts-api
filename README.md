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

## Run React Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

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

curl -X POST "http://localhost:8000/stt/binary?model=nova-3" \
  -H "Content-Type: audio/wav" \
  --data-binary @sample.wav

curl -X POST http://localhost:8000/stt/base64 \
  -H "Content-Type: application/json" \
  -d '{"audio_base64":"<base64-audio>","content_type":"audio/wav","model":"nova-3"}'

curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello from Deepgram","voice_model":"aura-2-thalia-en"}'
```

## Tests

```bash
pytest
```
