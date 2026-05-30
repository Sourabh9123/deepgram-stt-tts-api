import {
  Activity,
  AudioLines,
  CheckCircle2,
  Clipboard,
  FileAudio,
  Gauge,
  Loader2,
  Mic2,
  Play,
  Radio,
  RotateCcw,
  Send,
  Sparkles,
  Upload,
  Volume2,
  Wand2,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const STT_MODES = [
  { id: "multipart", label: "File", icon: Upload },
  { id: "binary", label: "Binary", icon: Radio },
  { id: "base64", label: "Base64", icon: Clipboard },
];
const VOICES = [
  "aura-2-thalia-en",
  "aura-2-asteria-en",
  "aura-2-luna-en",
  "aura-2-orion-en",
  "aura-2-arcas-en",
];

function formatBytes(value) {
  if (!value) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  return `${(value / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function buildAudioUrl(audioUrl) {
  if (!audioUrl) return "";
  if (audioUrl.startsWith("http")) return audioUrl;
  return `${API_BASE_URL}${audioUrl}`;
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const message = typeof payload === "string" ? payload : payload.detail || "Request failed";
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return payload;
}

function App() {
  const [health, setHealth] = useState(null);
  const [healthError, setHealthError] = useState("");
  const [sttMode, setSttMode] = useState("multipart");
  const [audioFile, setAudioFile] = useState(null);
  const [base64Audio, setBase64Audio] = useState("");
  const [contentType, setContentType] = useState("audio/wav");
  const [sttModel, setSttModel] = useState("nova-3");
  const [sttResult, setSttResult] = useState(null);
  const [sttError, setSttError] = useState("");
  const [sttLoading, setSttLoading] = useState(false);
  const [ttsText, setTtsText] = useState("Welcome to the Deepgram voice console.");
  const [voiceModel, setVoiceModel] = useState(VOICES[0]);
  const [ttsResult, setTtsResult] = useState(null);
  const [ttsError, setTtsError] = useState("");
  const [ttsLoading, setTtsLoading] = useState(false);

  const fileMeta = useMemo(() => {
    if (!audioFile) return "No file";
    return `${audioFile.name} | ${formatBytes(audioFile.size)}`;
  }, [audioFile]);

  useEffect(() => {
    let ignore = false;
    async function loadHealth() {
      try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const payload = await parseResponse(response);
        if (!ignore) setHealth(payload);
      } catch (error) {
        if (!ignore) setHealthError(error.message);
      }
    }
    loadHealth();
    return () => {
      ignore = true;
    };
  }, []);

  async function transcribeAudio() {
    setSttLoading(true);
    setSttError("");
    setSttResult(null);
    try {
      let response;
      if (sttMode === "multipart") {
        if (!audioFile) throw new Error("Select an audio file first");
        const formData = new FormData();
        formData.append("file", audioFile);
        response = await fetch(`${API_BASE_URL}/stt`, { method: "POST", body: formData });
      }
      if (sttMode === "binary") {
        if (!audioFile) throw new Error("Select an audio file first");
        response = await fetch(`${API_BASE_URL}/stt/binary?model=${encodeURIComponent(sttModel)}`, {
          method: "POST",
          headers: { "Content-Type": audioFile.type || contentType },
          body: audioFile,
        });
      }
      if (sttMode === "base64") {
        response = await fetch(`${API_BASE_URL}/stt/base64`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            audio_base64: base64Audio.trim(),
            content_type: contentType,
            model: sttModel,
          }),
        });
      }
      const payload = await parseResponse(response);
      setSttResult(payload);
    } catch (error) {
      setSttError(error.message);
    } finally {
      setSttLoading(false);
    }
  }

  async function generateSpeech() {
    setTtsLoading(true);
    setTtsError("");
    setTtsResult(null);
    try {
      const response = await fetch(`${API_BASE_URL}/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: ttsText, voice_model: voiceModel }),
      });
      const payload = await parseResponse(response);
      setTtsResult(payload);
    } catch (error) {
      setTtsError(error.message);
    } finally {
      setTtsLoading(false);
    }
  }

  function resetStt() {
    setAudioFile(null);
    setBase64Audio("");
    setSttResult(null);
    setSttError("");
  }

  return (
    <main className="app-shell">
      <section className="topbar" aria-label="Project status">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">
            <AudioLines size={24} />
          </div>
          <div>
            <h1>Deepgram Voice Console</h1>
            <p>Speech-to-text and text-to-speech operations</p>
          </div>
        </div>
        <div className={`health-pill ${healthError ? "is-down" : "is-up"}`}>
          {healthError ? <XCircle size={18} /> : <CheckCircle2 size={18} />}
          <span>{healthError ? "API offline" : "API online"}</span>
        </div>
      </section>

      <section className="model-strip" aria-label="Model status">
        <div>
          <Mic2 size={18} />
          <span>{health?.stt_model || "nova-3"}</span>
        </div>
        <div>
          <Volume2 size={18} />
          <span>{health?.tts_model || VOICES[0]}</span>
        </div>
        <div>
          <Activity size={18} />
          <span>{API_BASE_URL}</span>
        </div>
      </section>

      <section className="workspace">
        <article className="tool-panel">
          <div className="panel-header">
            <div>
              <span className="eyebrow">STT</span>
              <h2>Transcribe Audio</h2>
            </div>
            <button className="icon-button" type="button" onClick={resetStt} title="Reset STT form">
              <RotateCcw size={18} />
            </button>
          </div>

          <div className="segmented" role="tablist" aria-label="Speech-to-text mode">
            {STT_MODES.map((mode) => {
              const Icon = mode.icon;
              return (
                <button
                  className={sttMode === mode.id ? "active" : ""}
                  key={mode.id}
                  type="button"
                  onClick={() => setSttMode(mode.id)}
                >
                  <Icon size={16} />
                  {mode.label}
                </button>
              );
            })}
          </div>

          {sttMode !== "base64" ? (
            <label className="dropzone">
              <FileAudio size={34} />
              <span>{fileMeta}</span>
              <input
                accept="audio/*"
                type="file"
                onChange={(event) => {
                  const selected = event.target.files?.[0] || null;
                  setAudioFile(selected);
                  if (selected?.type) setContentType(selected.type);
                }}
              />
            </label>
          ) : (
            <textarea
              className="base64-input"
              value={base64Audio}
              onChange={(event) => setBase64Audio(event.target.value)}
              placeholder="data:audio/webm;base64,..."
              rows={8}
            />
          )}

          <div className="field-grid">
            <label>
              <span>Model</span>
              <input value={sttModel} onChange={(event) => setSttModel(event.target.value)} />
            </label>
            <label>
              <span>Content type</span>
              <input value={contentType} onChange={(event) => setContentType(event.target.value)} />
            </label>
          </div>

          <button className="primary-button" type="button" onClick={transcribeAudio} disabled={sttLoading}>
            {sttLoading ? <Loader2 className="spin" size={18} /> : <Send size={18} />}
            Transcribe
          </button>

          {sttError ? <div className="error-banner">{sttError}</div> : null}
          {sttResult ? (
            <div className="result-panel">
              <div className="result-stat">
                <Gauge size={18} />
                <span>{Math.round((sttResult.confidence || 0) * 100)}%</span>
              </div>
              <p className="transcript">{sttResult.transcript || "No transcript returned."}</p>
              <dl className="metadata-list">
                <div>
                  <dt>Request</dt>
                  <dd>{sttResult.metadata?.request_id || "n/a"}</dd>
                </div>
                <div>
                  <dt>Duration</dt>
                  <dd>{sttResult.metadata?.duration || "n/a"}</dd>
                </div>
              </dl>
            </div>
          ) : null}
        </article>

        <article className="tool-panel accent-panel">
          <div className="panel-header">
            <div>
              <span className="eyebrow">TTS</span>
              <h2>Generate Speech</h2>
            </div>
            <div className="panel-icon" aria-hidden="true">
              <Sparkles size={20} />
            </div>
          </div>

          <label className="textarea-label">
            <span>Text</span>
            <textarea value={ttsText} onChange={(event) => setTtsText(event.target.value)} rows={9} />
          </label>

          <label className="select-label">
            <span>Voice</span>
            <select value={voiceModel} onChange={(event) => setVoiceModel(event.target.value)}>
              {VOICES.map((voice) => (
                <option key={voice} value={voice}>
                  {voice}
                </option>
              ))}
            </select>
          </label>

          <button className="primary-button warm" type="button" onClick={generateSpeech} disabled={ttsLoading}>
            {ttsLoading ? <Loader2 className="spin" size={18} /> : <Wand2 size={18} />}
            Generate MP3
          </button>

          {ttsError ? <div className="error-banner">{ttsError}</div> : null}
          {ttsResult ? (
            <div className="result-panel audio-result">
              <div className="audio-heading">
                <Play size={18} />
                <span>{ttsResult.voice_model}</span>
              </div>
              {ttsResult.audio_url ? <audio controls src={buildAudioUrl(ttsResult.audio_url)} /> : null}
              <dl className="metadata-list">
                <div>
                  <dt>Bytes</dt>
                  <dd>{formatBytes(ttsResult.bytes_written)}</dd>
                </div>
                <div>
                  <dt>File</dt>
                  <dd>{ttsResult.file_path}</dd>
                </div>
              </dl>
            </div>
          ) : null}
        </article>
      </section>
    </main>
  );
}

export default App;
