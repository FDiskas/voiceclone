import { useState } from "react";

import { createProfile, transcribe } from "../api/client";
import { AudioSource } from "./AudioSource";

interface Props {
  onCreated: () => void;
}

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "lt", label: "Lithuanian" },
  { code: "de", label: "German" },
  { code: "fr", label: "French" },
  { code: "es", label: "Spanish" },
  { code: "pt-BR", label: "Portuguese (Brazil)" },
  { code: "ru", label: "Russian" },
  { code: "zh", label: "Chinese" },
];

export function CreateProfile({ onCreated }: Props) {
  const [name, setName] = useState("");
  const [language, setLanguage] = useState("en");
  const [transcript, setTranscript] = useState("");
  const [audio, setAudio] = useState<Blob | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
