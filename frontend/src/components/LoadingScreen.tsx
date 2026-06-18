// Full-screen startup splash shown while the backend sidecar is coming online.
// Dismissed automatically once useStatusLog transitions out of "connecting".
export function LoadingScreen() {
  return (
    <div className="loading-screen" role="status" aria-label="Starting VoiceClone">
      <div className="loading-screen__content">
        {/* Animated logo ring */}
        <div className="loading-screen__ring" aria-hidden="true">
          <div className="loading-screen__ring-track" />
          <div className="loading-screen__ring-arc" />
          <span className="loading-screen__logo">🎙️</span>
        </div>

        <h1 className="loading-screen__title">VoiceClone</h1>
        <p className="loading-screen__subtitle">Starting backend…</p>

        {/* Animated dot trail */}
        <div className="loading-screen__dots" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>

        <p className="loading-screen__hint">
          First launch may take a moment while the backend initialises.
        </p>
      </div>
    </div>
  );
}
