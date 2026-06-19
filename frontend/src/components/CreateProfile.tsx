import { useEffect, useState } from "react";

import { audioDurationSeconds } from "../api/audio";
import { createProfile, transcribe } from "../api/client";
import { LANGUAGES } from "../constants/languages";
import { AudioSource } from "./AudioSource";

interface Props {
  onCreated: () => void;
  // The language preselected for a new profile (a user preference from Settings).
  defaultLanguage: string;
}

// Reference clips longer than this trigger a quality/perf warning. OmniVoice
// clones best from a short sample; long references slow generation and hurt
// fidelity. Keep the recommended range in sync with the warning copy below.
const REFERENCE_WARN_SECONDS = 20;

export function CreateProfile({ onCreated, defaultLanguage }: Props) {
  const [name, setName] = useState("");
  const [language, setLanguage] = useState(defaultLanguage);
  const [transcript, setTranscript] = useState("");
  const [audio, setAudio] = useState<Blob | null>(null);
  const [audioDuration, setAudioDuration] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Measure the reference clip whenever it changes, so we can warn about
  // overly long samples. Ignore decode failures — duration is advisory only.
  useEffect(() => {
    if (!audio) {
      setAudioDuration(null);
      return;
    }
    let cancelled = false;
    setAudioDuration(null);
    audioDurationSeconds(audio)
      .then((seconds) => {
        if (!cancelled) setAudioDuration(seconds);
      })
      .catch(() => {
        if (!cancelled) setAudioDuration(null);
      });
    return () => {
      cancelled = true;
    };
  }, [audio]);

  const referenceTooLong = audioDuration != null && audioDuration > REFERENCE_WARN_SECONDS;

  const canSubmit = name.trim() && audio && !submitting;

  const handleAutoTranscribe = async () => {
    if (!audio) return;
    setTranscribing(true);
    setError(null);
    try {
      setTranscript(await transcribe(audio, language));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Transcription failed.");
    } finally {
      setTranscribing(false);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!audio) return;
    setSubmitting(true);
    setError(null);
    try {
      await createProfile({ name, language, transcript, audio });
      setName("");
      setTranscript("");
      setAudio(null);
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create profile.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2>Create a voice profile</h2>

      <label>
        Profile name
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="My voice" />
      </label>

      <label>
        Language
        <select value={language} onChange={(e) => setLanguage(e.target.value)}>
          {LANGUAGES.map((l) => (
            <option key={l.code} value={l.code}>
              {l.label}
            </option>
          ))}
        </select>
      </label>

      <span className="label-text">Reference voice</span>
      <AudioSource onChange={setAudio} />

      {referenceTooLong && audioDuration != null && (
        <p className="warning" role="status">
          Reference audio is {audioDuration.toFixed(1)}s long (&gt;{REFERENCE_WARN_SECONDS}s). This
          may cause slower generation, higher memory usage, and degraded voice cloning quality. We
          recommend trimming it to 3–10s.
        </p>
      )}

      <div className="transcript-header">
        <span className="label-text">Transcript (optional)</span>
        <button
          type="button"
          className="link"
          disabled={!audio || transcribing}
          onClick={handleAutoTranscribe}
        >
          {transcribing ? "Transcribing…" : "✦ Auto-transcribe"}
        </button>
      </div>
      <textarea
        value={transcript}
        onChange={(e) => setTranscript(e.target.value)}
        placeholder="Leave blank to auto-transcribe, or type exactly what you say in the recording."
        rows={3}
      />

      {error && <p className="error">{error}</p>}

      <button type="submit" className="primary" disabled={!canSubmit}>
        {submitting ? "Creating…" : "Create profile"}
      </button>
    </form>
  );
}
