import { useCallback, useState } from "react";

import { deleteProfile, listProfiles } from "../api/client";
import type { Profile } from "../api/types";

interface Profiles {
  profiles: Profile[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  remove: (id: string) => Promise<void>;
}

export function useProfiles(): Profiles {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setProfiles(await listProfiles());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load profiles.");
    } finally {
      setLoading(false);
    }
  }, []);

  const remove = useCallback(
    async (id: string) => {
      await deleteProfile(id);
      await refresh();
    },
    [refresh],
  );

  // Note: this hook does not self-load on mount. The backend is often still
  // starting then, so the caller (App) triggers `refresh` once the backend is
  // reachable — and again on every reconnect.
  return { profiles, loading, error, refresh, remove };
}
