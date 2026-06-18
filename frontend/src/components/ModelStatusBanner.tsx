import type { EngineStatus } from "../api/types";

interface Props {
  status: EngineStatus | null;
}

// Shows a download/load indicator while the voice model becomes ready. Hidden
// once ready/idle (the default `fake` dev engine reports ready instantly, so
// this never appears in development). On first desktop launch the model is
// fetched from Hugging Face, which can take several minutes.
export function ModelStatusBanner({ status }: Props) {
  if (!status) return null;

  if (status.state === "error") {
    return (
      <div className="model-banner model-banner--error" role="alert">
        <strong>Voice model failed to load.</strong>
        {status.detail && <span className="muted">{status.detail}</span>}
      </div>
    );
  }

  if (status.state !== "downloading" && status.state !== "loading") return null;

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
