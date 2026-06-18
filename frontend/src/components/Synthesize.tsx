import { useState } from "react";

import { synthesize, synthesizeStream } from "../api/client";
import type { Profile } from "../api/types";
import { StreamingAudioPlayer } from "../audio/streamingPlayer";

interface Props {
  profile: Profile;
}

export function Synthesize({ profile }: Props) {
  const [text, setText] = useState("");
  const [speed, setSpeed] = useState(1.0);
  const [streaming, setStreaming] = useState(true);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSpeak = async () => {
    setBusy(true);
    setError(null);
    try {
      if (streaming) {
        await playStreamed();
      } else {
        await playWhole();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Synthesis failed.");
    } finally {
      setBusy(false);
    }
  };

  const playWhole = async () => {
    const blob = await synthesize(profile.id, { text, speed });
    setAudioUrl((previous) => {
      if (previous) URL.revokeObjectURL(previous);
      return URL.createObjectURL(blob);
    });
  };

  const playStreamed = async () => {
    setAudioUrl(null);
    const player = new StreamingAudioPlayer();
    try {
      await synthesizeStream(profile.id, { text, speed }, (wav) => {
        void player.enqueue(wav);
      });
    } finally {
      void player.close();
    }
  };

  return (
    <div className="card">
      <h2>
        Speak as <em>{profile.name}</em>
      </h2>

      <label>
        Text to speak
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type what this voice should say…"
          rows={4}
        />
      </label>

      <label>
        Speed: {speed.toFixed(2)}×
        <input
          type="range"
          min={0.5}
          max={2}
          step={0.05}
          value={speed}
          onChange={(e) => setSpeed(Number(e.target.value))}
        />
      </label>

      <label className="checkbox">
        <input type="checkbox" checked={streaming} onChange={(e) => setStreaming(e.target.checked)} />
        Stream sentence-by-sentence (starts playing sooner)
      </label>

      {error && <p className="error">{error}</p>}

      <button type="button" className="primary" disabled={!text.trim() || busy} onClick={handleSpeak}>
        {busy ? "Synthesizing…" : "Generate speech"}
      </button>

      {audioUrl && <audio controls autoPlay src={audioUrl} />}
    </div>
  );
}
