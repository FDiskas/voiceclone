import { useState } from "react";

import { synthesize, synthesizeStream } from "../api/client";
import { concatWavChunks, saveBlob } from "../api/audio";
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
  const [autoPlay, setAutoPlay] = useState(false);
  const [downloadBlob, setDownloadBlob] = useState<Blob | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSpeak = async () => {
    setBusy(true);
    setError(null);
    setDownloadBlob(null);
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

  const showPlayer = (blob: Blob, play: boolean) => {
    setAutoPlay(play);
    setAudioUrl((previous) => {
      if (previous) URL.revokeObjectURL(previous);
      return URL.createObjectURL(blob);
    });
  };

  const playWhole = async () => {
    const blob = await synthesize(profile.id, { text, speed });
    setDownloadBlob(blob);
    showPlayer(blob, true);
  };

  const playStreamed = async () => {
    setAudioUrl(null);
    const player = new StreamingAudioPlayer();
    // Keep a copy of each chunk so we can offer the full clip for download —
    // decodeAudioData in the player detaches the original buffer.
    const chunks: ArrayBuffer[] = [];
    try {
      await synthesizeStream(profile.id, { text, speed }, (wav) => {
        chunks.push(wav.slice(0));
        void player.enqueue(wav);
      });
    } finally {
      void player.close();
    }
    const blob = concatWavChunks(chunks);
    setDownloadBlob(blob);
    // Surface a player for the assembled clip so it can be replayed/scrubbed.
    // No autoplay — it already played live as it streamed.
    if (blob) showPlayer(blob, false);
  };

  const handleDownload = () => {
    if (downloadBlob) void saveBlob(downloadBlob, `${profile.name}.wav`);
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

      {audioUrl && <audio controls autoPlay={autoPlay} src={audioUrl} />}

      {downloadBlob && (
        <button type="button" className="link" onClick={handleDownload}>
          ↓ Download audio
        </button>
      )}
    </div>
  );
}
