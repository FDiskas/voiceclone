import { useCallback, useEffect, useRef, useState } from "react";

import { getEngineStatus } from "../api/client";
import type { EngineStatus } from "../api/types";

const POLL_INTERVAL_MS = 1500;

export interface EngineStatusState {
  status: EngineStatus | null;
  refresh: () => Promise<void>;
}

// Whether the engine is in a transient state that warrants continued polling.
// "idle" is a resting state now (the model loads on demand, not at startup), so
// we stop polling there and resume once the user triggers a download — see
// `refresh`, which the Download button calls after POSTing /warmup.
function shouldKeepPolling(state: string): boolean {
  return state === "downloading" || state === "loading";
}

// Polls the backend's engine readiness while the model is actively becoming
// ready (idle → downloading → loading → ready|error). Stops once the state
// settles on "ready" or "error". `refresh` re-fetches on demand (after a
// download is triggered or a model deleted) and resumes polling if busy again.
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
