import { useCallback, useEffect, useRef, useState } from "react";

import { getEngineStatus } from "../api/client";
import type { EngineStatus } from "../api/types";

const POLL_INTERVAL_MS = 1500;

export interface EngineStatusState {
  status: EngineStatus | null;
  refresh: () => Promise<void>;
}

// Polls the backend's engine readiness while the model is actively
// downloading/loading and stops once it settles (ready/error/idle). `refresh`
// re-fetches on demand (e.g. after deleting the model) and resumes polling if
// the engine is busy again. Returns null status until the first poll lands.
export function useEngineStatus(): EngineStatusState {
  const [status, setStatus] = useState<EngineStatus | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout>>();
  const cancelled = useRef(false);

  const tick = useCallback(async () => {
    try {
      const next = await getEngineStatus();
      if (cancelled.current) return;
      setStatus(next);
      // Keep polling only while the model is still becoming ready.
      if (next.state === "downloading" || next.state === "loading") {
        timer.current = setTimeout(tick, POLL_INTERVAL_MS);
      }
    } catch {
      if (cancelled.current) return;
      // Backend not up yet (sidecar still starting) — retry.
      timer.current = setTimeout(tick, POLL_INTERVAL_MS);
    }
  }, []);

  const refresh = useCallback(async () => {
    clearTimeout(timer.current);
    await tick();
  }, [tick]);

  useEffect(() => {
    cancelled.current = false;
    void tick();
    return () => {
      cancelled.current = true;
      clearTimeout(timer.current);
    };
  }, [tick]);

  return { status, refresh };
}
