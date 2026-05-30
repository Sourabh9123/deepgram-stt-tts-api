import {
  Activity,
  AudioLines,
  CheckCircle2,
  Clipboard,
  FileAudio,
  Gauge,
  Headphones,
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
import { useEffect, useMemo, useRef, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const STT_MODES = [
  { id: "recording", label: "Mic", icon: Mic2 },
  { id: "multipart", label: "File", icon: Upload },
  { id: "binary", label: "Binary", icon: Radio },
  { id: "base64", label: "Base64", icon: Clipboard },
];
const RECORDER_MIME_TYPES = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"];
const STT_LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "Hindi" },
  { code: "es", label: "Spanish" },
  { code: "fr", label: "French" },
  { code: "de", label: "German" },
  { code: "it", label: "Italian" },
  { code: "pt", label: "Portuguese" },
  { code: "ja", label: "Japanese" },
  { code: "ko", label: "Korean" },
  { code: "zh", label: "Chinese" },
];
const TTS_LANGUAGE_GROUPS = [
  {
    code: "en",
    label: "English",
    voices: ["aura-2-thalia-en", "aura-2-asteria-en", "aura-2-luna-en", "aura-2-orion-en", "aura-2-arcas-en"],
  },
  { code: "es", label: "Spanish", voices: ["aura-2-celeste-es", "aura-2-estrella-es", "aura-2-nestor-es"] },
  { code: "fr", label: "French", voices: ["aura-2-agathe-fr", "aura-2-hector-fr"] },
  { code: "de", label: "German", voices: ["aura-2-julius-de", "aura-2-viktoria-de", "aura-2-elara-de"] },
  { code: "it", label: "Italian", voices: ["aura-2-livia-it", "aura-2-dionisio-it", "aura-2-melia-it"] },
  { code: "nl", label: "Dutch", voices: ["aura-2-rhea-nl", "aura-2-sander-nl", "aura-2-beatrix-nl"] },
  { code: "ja", label: "Japanese", voices: ["aura-2-fujin-ja", "aura-2-izanami-ja", "aura-2-uzume-ja"] },
  { code: "hi", label: "Hindi", voices: [] },
];
const DEFAULT_TTS_LANGUAGE = "en";
const DEFAULT_TTS_VOICE = TTS_LANGUAGE_GROUPS.find((group) => group.code === DEFAULT_TTS_LANGUAGE).voices[0];

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

function getRecorderMimeType() {
  if (typeof MediaRecorder === "undefined") return "";
  return RECORDER_MIME_TYPES.find((type) => MediaRecorder.isTypeSupported(type)) || "";
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
  const [sttMode, setSttMode] = useState("recording");
  const [audioFile, setAudioFile] = useState(null);
  const [base64Audio, setBase64Audio] = useState("");
  const [contentType, setContentType] = useState("audio/webm");
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [recordingUrl, setRecordingUrl] = useState("");
  const [recording, setRecording] = useState(false);
  const [monitorEnabled, setMonitorEnabled] = useState(false);
  const [sttModel, setSttModel] = useState("nova-3");
  const [sttLanguage, setSttLanguage] = useState("en");
  const [sttResult, setSttResult] = useState(null);
  const [sttError, setSttError] = useState("");
  const [sttLoading, setSttLoading] = useState(false);
  const [ttsText, setTtsText] = useState("Welcome to the Deepgram voice console.");
  const [ttsLanguage, setTtsLanguage] = useState(DEFAULT_TTS_LANGUAGE);
  const [voiceModel, setVoiceModel] = useState(DEFAULT_TTS_VOICE);
  const [ttsResult, setTtsResult] = useState(null);
  const [ttsError, setTtsError] = useState("");
  const [ttsLoading, setTtsLoading] = useState(false);
  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const liveAudioRef = useRef(null);
  const audioChunksRef = useRef([]);

  const fileMeta = useMemo(() => {
    if (!audioFile) return "No file";
    return `${audioFile.name} | ${formatBytes(audioFile.size)}`;
  }, [audioFile]);
  const ttsLanguageGroup = useMemo(
    () => TTS_LANGUAGE_GROUPS.find((group) => group.code === ttsLanguage) || TTS_LANGUAGE_GROUPS[0],
    [ttsLanguage],
  );
  const ttsVoices = ttsLanguageGroup.voices;
  const ttsUnsupported = ttsVoices.length === 0;

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

  useEffect(() => {
    if (!recordedBlob) {
      setRecordingUrl("");
      return undefined;
    }
    const url = URL.createObjectURL(recordedBlob);
    setRecordingUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [recordedBlob]);

  useEffect(() => {
    return () => {
      stopRecordingTracks();
    };
  }, []);

  useEffect(() => {
    if (!recording || !mediaStreamRef.current) return;
    if (monitorEnabled) {
      playLiveMonitor(mediaStreamRef.current);
      return;
    }
    stopLiveMonitor();
  }, [monitorEnabled, recording]);

  useEffect(() => {
    if (ttsVoices.length === 0) {
      setVoiceModel("");
      return;
    }
    if (!ttsVoices.includes(voiceModel)) setVoiceModel(ttsVoices[0]);
  }, [ttsVoices, voiceModel]);

  function stopLiveMonitor() {
    if (!liveAudioRef.current) return;
    liveAudioRef.current.pause();
    liveAudioRef.current.srcObject = null;
  }

  function stopRecordingTracks() {
    stopLiveMonitor();
    mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    mediaStreamRef.current = null;
  }

  async function playLiveMonitor(stream) {
    if (!monitorEnabled || !liveAudioRef.current) return;
    liveAudioRef.current.srcObject = stream;
    liveAudioRef.current.muted = false;
    liveAudioRef.current.volume = 1;
    try {
      await liveAudioRef.current.play();
    } catch {
      setSttError("Mic monitor is blocked by the browser. Use the recording playback after stopping.");
    }
  }

  async function startRecording() {
    setSttError("");
    setSttResult(null);
    setRecordedBlob(null);
    try {
      if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
        throw new Error("Browser audio recording is not available");
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = getRecorderMimeType();
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      audioChunksRef.current = [];
      mediaStreamRef.current = stream;
      mediaRecorderRef.current = recorder;
      await playLiveMonitor(stream);

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const type = recorder.mimeType || mimeType || "audio/webm";
        const blob = new Blob(audioChunksRef.current, { type });
        setRecordedBlob(blob);
        setContentType(type);
        setRecording(false);
        stopRecordingTracks();
      };
      recorder.start();
      setRecording(true);
    } catch (error) {
      setRecording(false);
      stopRecordingTracks();
      setSttError(error.message);
    }
  }

  function stopRecording() {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
      return;
    }
    setRecording(false);
    stopRecordingTracks();
  }

  async function transcribeAudio() {
    setSttLoading(true);
    setSttError("");
    setSttResult(null);
    try {
      let response;
      if (sttMode === "recording") {
        if (!recordedBlob) throw new Error("Record audio first");
        response = await fetch(
          `${API_BASE_URL}/stt/recording?model=${encodeURIComponent(sttModel)}&language=${encodeURIComponent(sttLanguage)}`,
          {
            method: "POST",
            headers: { "Content-Type": recordedBlob.type || contentType || "audio/webm" },
            body: recordedBlob,
          },
        );
      }
      if (sttMode === "multipart") {
        if (!audioFile) throw new Error("Select an audio file first");
        const formData = new FormData();
        formData.append("file", audioFile);
        response = await fetch(`${API_BASE_URL}/stt?language=${encodeURIComponent(sttLanguage)}`, {
          method: "POST",
          body: formData,
        });
      }
      if (sttMode === "binary") {
        if (!audioFile) throw new Error("Select an audio file first");
        response = await fetch(
          `${API_BASE_URL}/stt/binary?model=${encodeURIComponent(sttModel)}&language=${encodeURIComponent(sttLanguage)}`,
          {
            method: "POST",
            headers: { "Content-Type": audioFile.type || contentType },
            body: audioFile,
          },
        );
      }
      if (sttMode === "base64") {
        response = await fetch(`${API_BASE_URL}/stt/base64`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            audio_base64: base64Audio.trim(),
            content_type: contentType,
            model: sttModel,
            language: sttLanguage,
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
      if (ttsUnsupported) {
        throw new Error(`${ttsLanguageGroup.label} is not currently available in Deepgram Aura TTS.`);
      }
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
    stopRecording();
    setAudioFile(null);
    setBase64Audio("");
    setRecordedBlob(null);
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
          <span>{health?.tts_model || DEFAULT_TTS_VOICE}</span>
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
              <h2>Speak to Write</h2>
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

          {sttMode === "recording" ? (
            <div className={`recording-panel ${recording ? "is-recording" : ""}`}>
              <div className="recording-status">
                <span className="recording-dot" aria-hidden="true" />
                <span>{recording ? "Recording" : recordedBlob ? `Ready | ${formatBytes(recordedBlob.size)}` : "Ready"}</span>
              </div>
              <label className="monitor-toggle">
                <input type="checkbox" checked={monitorEnabled} onChange={(event) => setMonitorEnabled(event.target.checked)} />
                <Headphones size={18} />
                <span>Monitor</span>
              </label>
              <button
                className="secondary-button"
                type="button"
                onClick={recording ? stopRecording : startRecording}
                disabled={sttLoading}
              >
                {recording ? <XCircle size={18} /> : <Mic2 size={18} />}
                {recording ? "Stop" : recordedBlob ? "Record Again" : "Start"}
              </button>
              <audio ref={liveAudioRef} className="live-monitor" aria-label="Live microphone monitor" />
              {recordingUrl && !recording ? (
                <div className="recording-playback">
                  <div className="audio-heading">
                    <Play size={18} />
                    <span>Recording Playback</span>
                  </div>
                  <audio controls preload="metadata" src={recordingUrl} />
                </div>
              ) : null}
            </div>
          ) : sttMode !== "base64" ? (
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
              <span>Language</span>
              <select value={sttLanguage} onChange={(event) => setSttLanguage(event.target.value)}>
                {STT_LANGUAGES.map((language) => (
                  <option key={language.code} value={language.code}>
                    {language.label}
                  </option>
                ))}
              </select>
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
              {sttResult.transcript ? (
                <button className="secondary-button compact" type="button" onClick={() => setTtsText(sttResult.transcript)}>
                  <Volume2 size={18} />
                  Use For Speech
                </button>
              ) : null}
            </div>
          ) : null}
        </article>

        <article className="tool-panel accent-panel">
          <div className="panel-header">
            <div>
              <span className="eyebrow">TTS</span>
              <h2>Write to Speak</h2>
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
            <span>Language</span>
            <select value={ttsLanguage} onChange={(event) => setTtsLanguage(event.target.value)}>
              {TTS_LANGUAGE_GROUPS.map((language) => (
                <option key={language.code} value={language.code}>
                  {language.voices.length ? language.label : `${language.label} - unavailable`}
                </option>
              ))}
            </select>
          </label>

          <label className="select-label">
            <span>Voice</span>
            <select value={voiceModel} onChange={(event) => setVoiceModel(event.target.value)} disabled={ttsUnsupported}>
              {ttsVoices.map((voice) => (
                <option key={voice} value={voice}>
                  {voice}
                </option>
              ))}
            </select>
          </label>

          {ttsUnsupported ? <div className="notice-banner">Deepgram Aura TTS does not currently include a Hindi voice.</div> : null}

          <button className="primary-button warm" type="button" onClick={generateSpeech} disabled={ttsLoading || ttsUnsupported}>
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
