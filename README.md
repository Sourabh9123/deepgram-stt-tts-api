# Deepgram STT/TTS Voice Console

Production-ready FastAPI and React integration for Deepgram speech-to-text and text-to-speech.

The app includes:

- FastAPI backend with async Deepgram client services.
- React voice console for file upload, browser microphone recording, base64 audio, and text-to-speech.
- Browser mic recording with optional live monitor and playback.
- Speech-to-text language selection.
- Language-aware TTS voice selection for Deepgram Aura voices.
- Password-protected Swagger, ReDoc, and OpenAPI schema.
- Docker Compose setup for API and frontend.
- Black/isort formatting and pytest coverage.

## Project Layout

```text
app/
  api/
    deps.py
    routes/
      docs.py
      health.py
      stt.py
      tts.py
  config/settings.py
  services/
    deepgram_client.py
    stt_service.py
    tts_service.py
frontend/
  src/App.jsx
  src/styles.css
tests/
examples/
docker-compose.yml
Makefile
pyproject.toml
```

## Environment

Create backend environment variables:

```bash
cp .env.example .env
```

Set at least:

```env
DEEPGRAM_API_KEY=replace-with-your-deepgram-api-key
```

Backend env variables:

```env
DEEPGRAM_API_KEY=replace-with-your-deepgram-api-key
DEEPGRAM_BASE_URL=https://api.deepgram.com/v1
DEFAULT_STT_MODEL=nova-3
DEFAULT_STT_LANGUAGE=en
DEFAULT_TTS_MODEL=aura-2-thalia-en
AUDIO_OUTPUT_DIR=generated_audio
REQUEST_TIMEOUT_SECONDS=60
LOG_LEVEL=INFO
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DOCS_USERNAME=admin
DOCS_PASSWORD=change-me
```

Create frontend environment variables for local development:

```bash
cd frontend
cp .env.example .env
```

Frontend env:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Run With Docker

Recommended for the full stack:

```bash
docker compose up --build -d
```

Or:

```bash
make docker-up
```

Open:

```text
Frontend: http://localhost:5173
API:      http://localhost:8000
Docs:     http://localhost:8000/docs
```

Check running containers:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs api
docker compose logs frontend
```

Important browser note: use `http://localhost:5173` unless you also add your exact frontend origin to `CORS_ALLOWED_ORIGINS`.

## Run Locally

Install backend dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Install frontend dependencies:

```bash
cd frontend
npm install
cp .env.example .env
cd ..
```

Run both services:

```bash
make local
```

This starts:

- API at `http://localhost:8000`
- frontend at `http://localhost:5173`

You can also run them separately:

```bash
make api
make frontend
```

## Make Commands

```bash
make install          # install backend and frontend dependencies
make install-backend  # install Python dependencies
make install-frontend # install frontend dependencies
make local            # run API and frontend together
make api              # run FastAPI only
make frontend         # run React/Vite only
make test             # run pytest
make format           # run black and isort
make lint             # check black and isort
make build            # build frontend
make docker-up        # build and start Docker Compose detached
```

## API Docs

Docs are protected with HTTP Basic Auth.

Set these in `.env`:

```env
DOCS_USERNAME=admin
DOCS_PASSWORD=change-me
```

Then open:

```text
http://localhost:8000/docs
http://localhost:8000/redoc
http://localhost:8000/openapi.json
```

## Frontend Features

The React console supports:

- Mic recording with start/stop.
- Optional mic monitor so you can hear live input.
- Playback of recorded audio before transcription.
- File upload transcription.
- Raw binary transcription.
- Base64/data URL transcription.
- STT model and language controls.
- TTS language and voice controls.
- Generated MP3 playback.
- Reuse transcript as TTS input.

## Language Support

Speech-to-text supports a `language` parameter and defaults to:

```env
DEFAULT_STT_LANGUAGE=en
```

The frontend includes common STT languages such as English, Hindi, Spanish, French, German, Italian, Portuguese, Japanese, Korean, and Chinese.

Text-to-speech language support depends on available Deepgram Aura voices. The UI groups voices by supported language. Hindi TTS is shown as unavailable because Deepgram Aura does not currently provide a Hindi voice in this app's voice list.

## API Examples

Health check:

```bash
curl http://localhost:8000/health
```

Multipart file STT:

```bash
curl -X POST "http://localhost:8000/stt?language=en" \
  -F "file=@sample.wav"
```

Raw binary STT:

```bash
curl -X POST "http://localhost:8000/stt/binary?model=nova-3&language=en" \
  -H "Content-Type: audio/wav" \
  --data-binary @sample.wav
```

Browser recording STT:

```bash
curl -X POST "http://localhost:8000/stt/recording?model=nova-3&language=en" \
  -H "Content-Type: audio/webm" \
  --data-binary @recording.webm
```

Base64 STT:

```bash
curl -X POST http://localhost:8000/stt/base64 \
  -H "Content-Type: application/json" \
  -d '{"audio_base64":"<base64-audio>","content_type":"audio/wav","model":"nova-3","language":"en"}'
```

TTS:

```bash
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello from Deepgram","voice_model":"aura-2-thalia-en"}'
```

Generated audio is saved under `AUDIO_OUTPUT_DIR` and served from:

```text
http://localhost:8000/audio/<filename>
```

## Python Examples

```bash
python examples/transcribe_file.py ./sample.wav
python examples/generate_speech.py "Hello from Deepgram"
```

## Testing And Formatting

Run tests:

```bash
make test
```

Format Python:

```bash
make format
```

Check formatting:

```bash
make lint
```

Build frontend:

```bash
make build
```

## Troubleshooting

API not reachable:

```bash
docker compose ps
curl http://localhost:8000/health
docker compose logs api
```

Frontend cannot call API:

- Confirm `VITE_API_BASE_URL=http://localhost:8000`.
- Confirm frontend is opened at `http://localhost:5173`.
- Add any alternate frontend URL to `CORS_ALLOWED_ORIGINS`.

Docs ask for a password:

- This is expected.
- Use `DOCS_USERNAME` and `DOCS_PASSWORD` from `.env`.

Hindi text sounds English in TTS:

- Do not use an English Aura voice for Hindi text.
- The UI marks Hindi TTS unavailable because a Hindi Aura voice is not configured here.

Mic monitor causes echo:

- Use headphones when enabling Monitor.
- Or leave Monitor disabled and listen using Recording Playback after stopping.
