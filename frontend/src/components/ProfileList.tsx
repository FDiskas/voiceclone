import type { Profile } from "../api/types";

interface Props {
  profiles: Profile[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export function ProfileList({ profiles, selectedId, onSelect, onDelete }: Props) {
  if (profiles.length === 0) {
    return <p className="muted">No profiles yet. Create one to get started.</p>;
  }

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
        </li>
      ))}
    </ul>
  );
}
