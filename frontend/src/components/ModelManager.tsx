import { useState } from "react";

import { deleteEngineModel } from "../api/client";
import type { EngineStatus } from "../api/types";

interface Props {
  status: EngineStatus;
  // Called after a successful delete so the shared status can re-poll.
  onChanged: () => void;
}

function formatBytes(bytes: number): string {
  if (bytes <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** i).toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

// Lets the user delete the downloaded voice model to reclaim disk; it
// re-downloads the next time it's needed. Only rendered for an engine that has
// a managed model (status.manageable).
export function ModelManager({ status, onChanged }: Props) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Deleting mid-download would block on the in-flight load; keep it simple.
  const busyLoading = status.state === "downloading" || status.state === "loading";

  const handleDelete = async () => {
    if (!window.confirm("Delete the downloaded voice model? It will re-download the next time it's needed.")) {
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const result = await deleteEngineModel();
      setMessage(
        result.found
          ? `Deleted model — freed ${formatBytes(result.freed_bytes)}. It will re-download when next needed.`
          : "No downloaded model was found; nothing to delete.",
      );
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete the model.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card">
      <h2>Voice model</h2>
      <p className="muted">{status.message}</p>
      <div className="row">
        <button className="danger" onClick={handleDelete} disabled={busy || busyLoading}>
          {busy ? "Deleting…" : "Delete downloaded model"}
        </button>
        {busyLoading && <span className="muted">Available once the model finishes loading.</span>}
      </div>
      {message && <p className="muted">{message}</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
