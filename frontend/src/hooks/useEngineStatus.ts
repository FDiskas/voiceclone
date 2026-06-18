import { useCallback, useEffect, useRef, useState } from "react";

import { getEngineStatus } from "../api/client";
import type { EngineStatus } from "../api/types";

const POLL_INTERVAL_MS = 1500;

export interface EngineStatusState {
  status: EngineStatus | null;
  refresh: () => Promise<void>;
  retry: () => void;
}

// Whether the engine is in a transient state that warrants continued polling.
// "idle" is included because warm_up() fires at startup but the engine may
// still be in "idle" for a brief moment before it transitions to "loading" or
// "downloading" — stopping here would miss the entire progress window.
function shouldKeepPolling(state: string): boolean {
  return state === "downloading" || state === "loading" || state === "idle";
}

// Polls the backend's engine readiness while the model is actively becoming
// ready (idle → downloading → loading → ready|error). Stops once the state
// settles on "ready" or "error". `refresh` re-fetches on demand (e.g. after
// deleting the model) and resumes polling if the engine is busy again.
// `retry` restarts polling from an error state.
export function useEngineStatus(): EngineStatusState {
  const [status, setStatus] = useState<EngineStatus | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout>>();
  const cancelled = useRef(false);

  const tick = useCallback(async () => {
    try {
      const next = await getEngineStatus();
      if (cancelled.current) return;
      setStatus(next);
      if (shouldKeepPolling(next.state)) {
        timer.current = setTimeout(tick, POLL_INTERVAL_MS);
      }
    } catch {
      if (cancelled.current) return;
      // Backend not up yet (sidecar still starting) — keep retrying.
      timer.current = setTimeout(tick, POLL_INTERVAL_MS);
    }
  }, []);

  const refresh = useCallback(async () => {
    clearTimeout(timer.current);
    await tick();
  }, [tick]);

  // Restart polling from an error state (e.g. user clicks "Retry").
  const retry = useCallback(() => {
    clearTimeout(timer.current);
    setStatus(null);
    void tick();
  }, [tick]);

  useEffect(() => {
    cancelled.current = false;
    void tick();
    return () => {
      cancelled.current = true;
      clearTimeout(timer.current);
    };
  }, [tick]);

  return { status, refresh, retry };
}
