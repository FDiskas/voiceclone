import { useEffect, useRef, useState } from "react";

import { isAbortError, synthesize, synthesizeStream } from "../api/client";
import { concatWavChunks, saveBlob } from "../api/audio";
import type { Profile } from "../api/types";
import { StreamingAudioPlayer } from "../audio/streamingPlayer";
import { formatDuration } from "../format";

interface Props {
  profile: Profile;
}

// Keep in sync with `_MAX_SYNTHESIS_LENGTH` in backend/app/domain/values.py.
// The backend is the source of truth; this just gives immediate UI feedback
// instead of a round-trip rejection.
const MAX_SYNTHESIS_CHARS = 50_000;

export function Synthesize({ profile }: Props) {
  const [text, setText] = useState("");
  const [speed, setSpeed] = useState(1.0);
  const [streaming, setStreaming] = useState(true);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [autoPlay, setAutoPlay] = useState(false);
  const [downloadBlob, setDownloadBlob] = useState<Blob | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Streaming progress: how many sentences have rendered out of the total, and
  // an estimate of the seconds left (extrapolated from the average time per
  // completed sentence). Null when not streaming or before the total is known;
  // etaSeconds is null until the first sentence finishes.
  const [progress, setProgress] = useState<{
    done: number;
    total: number;
    etaSeconds: number | null;
  } | null>(null);
  // Lets the user cancel an in-flight synthesis. Held in a ref so the Stop
  // button and unmount cleanup can reach the current request.
  const abortRef = useRef<AbortController | null>(null);
  // Wall-clock start of the current stream, for the per-sentence ETA estimate.
  const streamStartRef = useRef(0);

  // Abort any in-flight request if the component goes away (e.g. the user
  // switches to another profile or view).
  useEffect(() => () => abortRef.current?.abort(), []);

  const charCount = text.length;
  const overLimit = charCount > MAX_SYNTHESIS_CHARS;

  const handleSpeak = async () => {
    const controller = new AbortController();
    abortRef.current = controller;
    setBusy(true);
    setError(null);
    setDownloadBlob(null);
    setProgress(null);
    try {
      if (streaming) {
        await playStreamed(controller.signal);
      } else {
        await playWhole(controller.signal);
      }
    } catch (err) {
      // A user-initiated cancel isn't an error — leave the UI clean.
      if (!isAbortError(err)) {
        setError(err instanceof Error ? err.message : "Synthesis failed.");
      }
    } finally {
      setBusy(false);
      setProgress(null);
      abortRef.current = null;
    }
  };

  const handleStop = () => abortRef.current?.abort();

  const showPlayer = (blob: Blob, play: boolean) => {
    setAutoPlay(play);
    setAudioUrl((previous) => {
      if (previous) URL.revokeObjectURL(previous);
      return URL.createObjectURL(blob);
    });
  };

  const playWhole = async (signal: AbortSignal) => {
    const blob = await synthesize(profile.id, { text, speed }, signal);
    setDownloadBlob(blob);
    showPlayer(blob, true);
  };

  const playStreamed = async (signal: AbortSignal) => {
    setAudioUrl(null);
    const player = new StreamingAudioPlayer();
    // Keep a copy of each chunk so we can offer the full clip for download —
    // decodeAudioData in the player detaches the original buffer.
    const chunks: ArrayBuffer[] = [];
    try {
      await synthesizeStream(
        profile.id,
        { text, speed },
        (wav) => {
          chunks.push(wav.slice(0));
          void player.enqueue(wav);
          // Read the clock outside the updater so it stays a pure function of
          // its previous state.
          const elapsed = (performance.now() - streamStartRef.current) / 1000;
          setProgress((prev) => {
            if (!prev) return prev;
            const done = prev.done + 1;
            const remaining = prev.total - done;
            // Average per-sentence time so far, extrapolated to what's left.
            const etaSeconds = remaining > 0 ? (elapsed / done) * remaining : null;
            return { ...prev, done, etaSeconds };
          });
        },
        (total) => {
          streamStartRef.current = performance.now();
          setProgress({ done: 0, total, etaSeconds: null });
        },
        signal,
      );
    } finally {
      void player.close();
    }
    // Cancelled mid-stream: discard the partial render rather than offering a
    // truncated clip.
    if (signal.aborted) return;
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
          aria-invalid={overLimit}
        />
        <span className={`char-count${overLimit ? " char-count--over" : ""}`} aria-live="polite">
          {charCount.toLocaleString()} / {MAX_SYNTHESIS_CHARS.toLocaleString()}
        </span>
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

      <div className="row">
        <button
          type="button"
          className="primary"
          disabled={!text.trim() || busy || overLimit}
          onClick={handleSpeak}
        >
          {busy ? "Synthesizing…" : "Generate speech"}
        </button>
        {busy && (
          <button type="button" className="danger" onClick={handleStop}>
            ◼ Stop
          </button>
        )}
      </div>

      {busy && progress && (
        <div className="synth-progress" aria-live="polite">
          <span className="muted">
            Synthesizing… {progress.done}/{progress.total} sentence{progress.total === 1 ? "" : "s"}
            {progress.etaSeconds != null && ` · ~${formatDuration(progress.etaSeconds)} left`}
          </span>
          <div className="progress">
            <div
              className="progress__bar"
              style={{ width: `${Math.round((progress.done / progress.total) * 100)}%` }}
            />
          </div>
        </div>
      )}

      {audioUrl && <audio controls autoPlay={autoPlay} src={audioUrl} />}

      {downloadBlob && (
        <button type="button" className="link" onClick={handleDownload}>
          ↓ Download audio
        </button>
      )}
    </div>
  );
}
