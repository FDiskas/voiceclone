import type { EngineStatus } from "../api/types";

interface Props {
  status: EngineStatus | null;
  onRetry?: () => void;
  // Begin downloading/loading the model (POST /warmup, then resume polling).
  onDownload?: () => void;
}

// Shows a download/load indicator while the voice model becomes ready.
//
// Visibility matrix:
//   null (first poll not yet landed) → subtle "connecting" strip
//   idle                             → "Download voice model" call-to-action
//   loading / downloading            → progress banner (spinner + bar)
//   ready                            → hidden (synthesis available)
//   error                            → error banner with retry
export function ModelStatusBanner({ status, onRetry, onDownload }: Props) {
  // Before the first poll lands show a minimal "connecting" hint so the
  // user knows the app is doing something (previously this was blank).
  if (!status) {
    return (
      <div className="model-banner model-banner--connecting" role="status" aria-live="polite">
        <div className="model-banner__row">
          <span className="model-banner__spinner" aria-hidden="true" />
          <span>Connecting to backend…</span>
        </div>
      </div>
    );
  }

  if (status.state === "error") {
    return (
      <div className="model-banner model-banner--error" role="alert">
        <div className="model-banner__row">
          <strong>Voice model failed to load.</strong>
          {status.detail && <span className="muted">{status.detail}</span>}
          {onRetry && (
            <button type="button" className="model-banner__retry" onClick={onRetry}>
              Retry
            </button>
          )}
        </div>
      </div>
    );
  }

  // Hidden once ready — synthesis is available, no need to show anything.
  if (status.state === "ready") return null;

  // Idle: the model isn't loaded and nothing is downloading yet. Offer an
  // explicit download instead of pulling hundreds of MB unprompted.
  if (status.state === "idle" && onDownload) {
    return (
      <div className="model-banner" role="status">
        <div className="model-banner__row">
          <span>Voice model isn’t loaded yet.</span>
          <button type="button" className="primary" onClick={onDownload}>
            Download voice model
          </button>
        </div>
        <p className="muted model-banner__hint">
          First run fetches the model from Hugging Face (a few hundred MB, once). Afterwards it just
          loads from cache.
        </p>
      </div>
    );
  }

  // downloading / loading — show progress bar.
  const pct = status.progress != null ? Math.round(status.progress * 100) : null;
  const indeterminate = pct == null;

  return (
    <div className="model-banner" role="status" aria-live="polite">
      <div className="model-banner__row">
        <span className="model-banner__spinner" aria-hidden="true" />
        <span>{status.message}</span>
        {pct != null && <span className="muted">{pct}%</span>}
      </div>
      <div className="progress" aria-hidden={indeterminate}>
        <div
          className={`progress__bar${indeterminate ? " progress__bar--indeterminate" : ""}`}
          style={indeterminate ? undefined : { width: `${pct}%` }}
        />
      </div>
      <p className="muted model-banner__hint">First run downloads the model — this happens once.</p>
    </div>
  );
}
