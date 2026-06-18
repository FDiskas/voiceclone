import { useState } from "react";

import { fetchProfileAudio } from "../api/client";
import { saveBlob } from "../api/audio";
import type { Profile } from "../api/types";

interface Props {
  profiles: Profile[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export function ProfileList({ profiles, selectedId, onSelect, onDelete }: Props) {
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  if (profiles.length === 0) {
    return <p className="muted">No profiles yet. Create one to get started.</p>;
  }

  const handleDownload = async (profile: Profile) => {
    setDownloadingId(profile.id);
    try {
      const blob = await fetchProfileAudio(profile.id);
      await saveBlob(blob, `${profile.name}.wav`);
    } catch {
      // A listed profile almost always has its audio on disk; stay quiet
      // rather than add per-row error chrome.
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <ul className="profile-list">
      {profiles.map((profile) => (
        <li
          key={profile.id}
          className={profile.id === selectedId ? "selected" : ""}
          onClick={() => onSelect(profile.id)}
        >
          <div>
            <strong>{profile.name}</strong>
            <span className="badge">{profile.language}</span>
          </div>
          <div className="profile-actions">
            <button
              type="button"
              className="link"
              disabled={downloadingId === profile.id}
              onClick={(e) => {
                e.stopPropagation();
                void handleDownload(profile);
              }}
            >
              {downloadingId === profile.id ? "Downloading…" : "Download"}
            </button>
            <button
              type="button"
              className="link-danger"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(profile.id);
              }}
            >
              Delete
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}
