import { useState } from "react";

import { CreateProfile } from "./components/CreateProfile";
import { ProfileList } from "./components/ProfileList";
import { Synthesize } from "./components/Synthesize";
import { useProfiles } from "./hooks/useProfiles";

export default function App() {
  const { profiles, loading, error, refresh, remove } = useProfiles();
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
        </section>
      </main>
    </div>
  );
}
