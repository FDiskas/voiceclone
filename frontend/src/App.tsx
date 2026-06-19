import { useEffect, useState } from "react";

import { warmupEngine } from "./api/client";
import { CreateProfile } from "./components/CreateProfile";
import { LoadingScreen } from "./components/LoadingScreen";
import { ModelStatusBanner } from "./components/ModelStatusBanner";
import { ProfileList } from "./components/ProfileList";
import { Settings } from "./components/Settings";
import { StatusBar } from "./components/StatusBar";
import { Synthesize } from "./components/Synthesize";
import { useDefaultLanguage } from "./hooks/useDefaultLanguage";
import { useEngineStatus } from "./hooks/useEngineStatus";
import { useProfiles } from "./hooks/useProfiles";
import { useStatusLog } from "./hooks/useStatusLog";

type View = "studio" | "settings";

export default function App() {
  const { profiles, loading, error, refresh, remove } = useProfiles();
  const { status: engineStatus, refresh: refreshEngine } = useEngineStatus();
  const { connStatus, logs, clearLogs, logPath } = useStatusLog();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [view, setView] = useState<View>("studio");
  const [defaultLanguage, setDefaultLanguage] = useDefaultLanguage();

  // Load (and reload) profiles whenever the backend becomes reachable. On a
  // cold start the backend is still booting, so the very first fetch has to
  // wait for this signal rather than firing on mount; a later reconnect
  // (ok → error → ok) refreshes the list too.
  useEffect(() => {
    if (connStatus === "ok") void refresh();
  }, [connStatus, refresh]);

  const selected = profiles.find((p) => p.id === selectedId) ?? null;

  const handleDelete = async (id: string) => {
    await remove(id);
    if (id === selectedId) setSelectedId(null);
  };

  // Start (or restart, from an error) the download/load, then re-poll so the
  // banner switches to a progress bar. warm_up is idempotent, so a re-click is
  // harmless; refresh runs even if the POST fails so the UI reflects reality.
  const handleDownloadModel = async () => {
    try {
      await warmupEngine();
    } finally {
      await refreshEngine();
    }
  };

  return (
    // Outer wrapper fills the viewport — the loading screen and the app body
    // both sit here so the fixed status bar is always rendered at the bottom.
    <div className="app-shell">
      {connStatus === "connecting" ? (
        <LoadingScreen />
      ) : (
        <div className="app">
          <header>
            <div>
              <h1>🎙️ VoiceClone</h1>
              <p className="muted">Record or upload a voice, then make it say anything.</p>
            </div>
            <nav className="nav">
              <button
                type="button"
                className={view === "studio" ? "nav__tab nav__tab--active" : "nav__tab"}
                onClick={() => setView("studio")}
              >
                Studio
              </button>
              <button
                type="button"
                className={view === "settings" ? "nav__tab nav__tab--active" : "nav__tab"}
                onClick={() => setView("settings")}
              >
                Settings
              </button>
            </nav>
          </header>

          <ModelStatusBanner
            status={engineStatus}
            onRetry={handleDownloadModel}
            onDownload={handleDownloadModel}
          />

          {view === "settings" ? (
            <Settings
              defaultLanguage={defaultLanguage}
              onChangeDefaultLanguage={setDefaultLanguage}
            />
          ) : (
            <main>
              <section className="column">
                <CreateProfile onCreated={refresh} defaultLanguage={defaultLanguage} />
              </section>

              <section className="column">
                <div className="card">
                  <h2>Your voices</h2>
                  {loading && <p className="muted">Loading…</p>}
                  {error && <p className="error">{error}</p>}
                  <ProfileList
                    profiles={profiles}
                    selectedId={selectedId}
                    onSelect={setSelectedId}
                    onDelete={handleDelete}
                  />
                </div>

                {selected && <Synthesize profile={selected} />}
              </section>
            </main>
          )}
        </div>
      )}

      {/* Status bar is always visible — including during the loading screen and
          the error state — so the user can see what's happening. */}
      <StatusBar connStatus={connStatus} logs={logs} clearLogs={clearLogs} logPath={logPath} />
    </div>
  );
}
