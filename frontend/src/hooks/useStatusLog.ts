/**
 * useStatusLog – tracks backend connectivity and collects timestamped API log
 * entries by patching the global `fetch`. Entries are capped at MAX_ENTRIES so
 * the list never grows unbounded.
 *
 * Connection states:
 *   "connecting"  – backend not yet reachable; still within the startup grace
 *                   period (CONNECT_TIMEOUT_MS). Loading screen is shown.
 *   "ok"          – last health-check succeeded; normal UI shown.
 *   "error"       – backend unreachable after grace period, or explicit spawn
 *                   failure event received from Tauri. Main UI shown with
 *                   status bar in error state.
 *
 * Noise suppression:
 *   - Internal polling URLs (/api/health, /api/engine/status) are excluded
 *     from the log — the status dot already communicates that state.
 *   - Consecutive identical messages are collapsed with a repeat counter.
 */
import { useCallback, useEffect, useRef, useState } from "react";

const HEALTH_URL = "/api/health";
const POLL_MS = 2_000;
const MAX_ENTRIES = 200;

// How long to stay in "connecting" (show loading screen) before giving up and
// transitioning to "error" when the backend never responds.
const CONNECT_TIMEOUT_MS = 15_000;

// URLs whose fetch results are never written to the log (internal polls).
const SILENT_PATTERNS = ["/api/health", "/api/engine/status"];

function isSilent(url: string): boolean {
  return SILENT_PATTERNS.some((p) => url.includes(p));
}

export type ConnStatus = "connecting" | "ok" | "error";

export interface LogEntry {
  id: number;
  ts: Date;
  level: "info" | "warn" | "error";
  message: string;
  /** How many consecutive times this exact message has been seen. */
  repeat: number;
}

export interface StatusLogState {
  connStatus: ConnStatus;
  logs: LogEntry[];
  clearLogs: () => void;
}

let _idSeq = 0;
const mkId = () => ++_idSeq;
const now = () => new Date();

// Module-level subscriber list so the patched fetch can notify all mounted
// hook instances without coupling to React internals.
type Subscriber = (entry: Omit<LogEntry, "repeat">) => void;
const subscribers = new Set<Subscriber>();

let fetchPatched = false;

function patchFetch() {
  if (fetchPatched) return;
  fetchPatched = true;

  const origFetch = window.fetch.bind(window);

  window.fetch = async (input, init) => {
    const url =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.toString()
          : (input as Request).url;

    const method = (
      init?.method ??
      (input instanceof Request ? input.method : "GET")
    ).toUpperCase();

    if (isSilent(url)) {
      return origFetch(input, init);
    }

    let response: Response;
    try {
      response = await origFetch(input, init);
    } catch (err) {
      publish({
        id: mkId(),
        ts: now(),
        level: "error",
        message: `${method} ${url} — network error: ${err instanceof Error ? err.message : String(err)}`,
      });
      throw err;
    }

    publish({
      id: mkId(),
      ts: now(),
      level: response.ok ? "info" : response.status >= 500 ? "error" : "warn",
      message: `${method} ${url} — ${response.status} ${response.statusText}`,
    });

    return response;
  };
}

function publish(entry: Omit<LogEntry, "repeat">) {
  subscribers.forEach((fn) => fn(entry));
}

/** Append or bump the repeat counter on the last entry if message matches. */
function appendOrRepeat(prev: LogEntry[], incoming: Omit<LogEntry, "repeat">): LogEntry[] {
  const last = prev[prev.length - 1];
  if (last && last.message === incoming.message && last.level === incoming.level) {
    const updated: LogEntry = { ...last, ts: incoming.ts, repeat: last.repeat + 1 };
    return [...prev.slice(0, -1), updated];
  }
  const entry: LogEntry = { ...incoming, repeat: 1 };
  const next = [...prev, entry];
  return next.length > MAX_ENTRIES ? next.slice(next.length - MAX_ENTRIES) : next;
}

/** Immediately add a log entry from outside the fetch patch (e.g. Tauri events). */
function makeLogEntry(
  level: LogEntry["level"],
  message: string,
): Omit<LogEntry, "repeat"> {
  return { id: mkId(), ts: now(), level, message };
}

export function useStatusLog(): StatusLogState {
  const [connStatus, setConnStatus] = useState<ConnStatus>("connecting");
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const timer = useRef<ReturnType<typeof setTimeout>>();
  const cancelled = useRef(false);
  const everConnected = useRef(false);
  const startedAt = useRef(Date.now());

  const addEntry = useCallback((entry: Omit<LogEntry, "repeat">) => {
    setLogs((prev) => appendOrRepeat(prev, entry));
  }, []);

  const clearLogs = useCallback(() => setLogs([]), []);

  // Patch fetch once per page load.
  useEffect(() => {
    patchFetch();
  }, []);

  // Subscribe to the patched fetch entries.
  useEffect(() => {
    subscribers.add(addEntry);
    return () => {
      subscribers.delete(addEntry);
    };
  }, [addEntry]);

  // Listen for backend:spawn-error events emitted by Rust when the sidecar
  // binary is missing or fails to start. Tauri v2 injects window.__TAURI__ into
  // the webview automatically — no extra npm package needed.
  useEffect(() => {
    // Guard: only runs inside the Tauri shell. In a plain browser __TAURI__ is absent.
    type TauriEvent = { payload: string };
    type TauriEventApi = {
      listen(event: string, handler: (ev: TauriEvent) => void): Promise<() => void>;
    };
    const api = (window as { __TAURI__?: { event?: TauriEventApi } }).__TAURI__?.event;
    if (!api) return;

    let unlisten: (() => void) | undefined;
    api
      .listen("backend:spawn-error", (ev) => {
        const msg = ev.payload || "Backend failed to start.";
        setConnStatus("error");
        addEntry(makeLogEntry("error", `Sidecar error: ${msg}`));
      })
      .then((fn) => { unlisten = fn; })
      .catch(() => { /* not in Tauri shell */ });

    return () => unlisten?.();
  }, [addEntry]);

  // Poll /api/health to track connection state (silently — not logged).
  const poll = useCallback(async () => {
    try {
      const res = await fetch(HEALTH_URL);
      if (cancelled.current) return;

      if (res.ok) {
        const body = await res.json().catch(() => ({}));
        const wasConnected = everConnected.current;
        everConnected.current = true;

        setConnStatus("ok");
        if (!wasConnected) {
          addEntry(
            makeLogEntry("info", `Backend connected — engine: ${body.engine ?? "unknown"}`),
          );
        }
      } else {
        if (cancelled.current) return;
        // Non-OK response (e.g. 500): always an error.
        setConnStatus("error");
      }
    } catch {
      if (cancelled.current) return;

      if (everConnected.current) {
        // Lost a connection that was previously working.
        setConnStatus("error");
      } else if (Date.now() - startedAt.current >= CONNECT_TIMEOUT_MS) {
        // Grace period expired — stop showing the loading screen.
        setConnStatus("error");
        addEntry(makeLogEntry("error", "Backend did not respond within 15 s. Is it running?"));
      }
      // else: still within grace period — stay "connecting" (loading screen).
    }

    if (!cancelled.current) {
      timer.current = setTimeout(poll, POLL_MS);
    }
  }, [addEntry]);

  useEffect(() => {
    cancelled.current = false;
    startedAt.current = Date.now();
    everConnected.current = false;
    void poll();
    return () => {
      cancelled.current = true;
      clearTimeout(timer.current);
    };
  }, [poll]);

  return { connStatus, logs, clearLogs };
}
