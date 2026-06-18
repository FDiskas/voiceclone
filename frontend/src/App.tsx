import { useState } from "react";

import { CreateProfile } from "./components/CreateProfile";
import { ModelManager } from "./components/ModelManager";
import { ModelStatusBanner } from "./components/ModelStatusBanner";
import { ProfileList } from "./components/ProfileList";
import { StatusBar } from "./components/StatusBar";
import { Synthesize } from "./components/Synthesize";
import { useEngineStatus } from "./hooks/useEngineStatus";
import { useProfiles } from "./hooks/useProfiles";
import { useStatusLog } from "./hooks/useStatusLog";

export default function App() {
  const { profiles, loading, error, refresh, remove } = useProfiles();
  const { status: engineStatus, refresh: refreshEngine, retry: retryEngine } = useEngineStatus();
  const { connStatus, logs, clearLogs } = useStatusLog();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selected = profiles.find((p) => p.id === selectedId) ?? null;

  const handleDelete = async (id: string) => {
    await remove(id);
    if (id === selectedId) setSelectedId(null);
  };

  return (
    <div className="app">
      <header>
        <h1>🎙️ VoiceClone</h1>
        <p className="muted">Record or upload a voice, then make it say anything — no sign-up.</p>
      </header>

      <ModelStatusBanner status={engineStatus} onRetry={retryEngine} />

      <main>
        <section className="column">
          <CreateProfile onCreated={refresh} />
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

          {engineStatus?.manageable && (
            <ModelManager status={engineStatus} onChanged={refreshEngine} />
          )}
        </section>
      </main>

      <StatusBar connStatus={connStatus} logs={logs} clearLogs={clearLogs} />
    </div>
  );
}
