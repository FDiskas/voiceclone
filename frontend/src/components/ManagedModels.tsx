import { useCallback, useEffect, useState } from "react";

import { deleteModel, listModels } from "../api/client";
import type { ManagedModel } from "../api/types";
import { formatBytes } from "../format";

// Lists downloadable models (voice engine, transcriber) with their real cache
// path and size, and lets the user delete each to reclaim disk. A deleted model
// re-downloads the next time it's needed.
export function ManagedModels() {
  const [models, setModels] = useState<ManagedModel[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setModels(await listModels());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load models.");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handleDelete = async (model: ManagedModel) => {
    if (!window.confirm(`Delete ${model.label}? It will re-download the next time it's needed.`)) {
      return;
    }
    setBusyKey(model.key);
    setError(null);
    setMessage(null);
    try {
      const result = await deleteModel(model.key);
      setMessage(
        result.found
          ? `Deleted ${model.label} — freed ${formatBytes(result.freed_bytes)}.`
          : `${model.label} wasn't downloaded; nothing to delete.`,
      );
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete the model.");
    } finally {
      setBusyKey(null);
    }
  };

  return (
    <div className="card">
      <h2>Models</h2>
      {models === null && !error && <p className="muted">Loading…</p>}
      {models !== null && models.length === 0 && (
        <p className="muted">No downloadable models — the fake engine needs no weights.</p>
      )}

      {models?.map((model) => (
        <div key={model.key} className="model-row">
          <div className="model-row__info">
            <strong>{model.label}</strong>
            <span className="muted">{model.repo_id}</span>
            {model.downloaded ? (
              <code className="model-row__path" title={model.path ?? undefined}>
                {model.path}
              </code>
            ) : (
              <span className="muted">Not downloaded yet.</span>
            )}
          </div>
          <div className="model-row__actions">
            {model.downloaded && <span className="muted">{formatBytes(model.size_bytes)}</span>}
            <button
              type="button"
              className="danger"
              disabled={!model.downloaded || busyKey === model.key}
              onClick={() => handleDelete(model)}
            >
              {busyKey === model.key ? "Deleting…" : "Delete"}
            </button>
          </div>
        </div>
      ))}

      {message && <p className="muted">{message}</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
