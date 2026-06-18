/**
 * useStatusLog – tracks backend connectivity and collects timestamped API log
 * entries by patching the global `fetch`. Entries are capped at MAX_ENTRIES so
 * the list never grows unbounded.
 *
 * Connection states:
 *   "connecting"  – no successful response yet since mount / last failure
 *   "ok"          – last health-check succeeded
 *   "error"       – backend unreachable or returned a server error
 */
import { useCallback, useEffect, useRef, useState } from "react";

const HEALTH_URL = "/api/health";
const POLL_MS = 3_000;
const MAX_ENTRIES = 200;

export type ConnStatus = "connecting" | "ok" | "error";

export interface LogEntry {
  id: number;
  ts: Date;
  level: "info" | "warn" | "error";
  message: string;
}

export interface StatusLogState {
  connStatus: ConnStatus;
  logs: LogEntry[];
  clearLogs: () => void;
}

let _idSeq = 0;
const mkId = () => ++_idSeq;

function now() {
  return new Date();
}

// Module-level subscriber list so the patched fetch can notify all mounted
// hook instances without coupling to React internals.
type Subscriber = (entry: LogEntry) => void;
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

    const method = (init?.method ?? (input instanceof Request ? input.method : "GET")).toUpperCase();

    // Don't log health-check polls — they'd flood the log.
    const isHealth = url.includes("/api/health");

    let response: Response;
    try {
      response = await origFetch(input, init);
    } catch (err) {
      if (!isHealth) {
        publish({
          id: mkId(),
          ts: now(),
          level: "error",
          message: `${method} ${url} — network error: ${err instanceof Error ? err.message : String(err)}`,
        });
      }
      throw err;
    }

    if (!isHealth) {
      const ok = response.ok;
      publish({
        id: mkId(),
        ts: now(),
        level: ok ? "info" : response.status >= 500 ? "error" : "warn",
        message: `${method} ${url} — ${response.status} ${response.statusText}`,
      });
    }

    return response;
  };
}

function publish(entry: LogEntry) {
  subscribers.forEach((fn) => fn(entry));
}

export function useStatusLog(): StatusLogState {
  const [connStatus, setConnStatus] = useState<ConnStatus>("connecting");
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const timer = useRef<ReturnType<typeof setTimeout>>();
  const cancelled = useRef(false);

  const addEntry = useCallback((entry: LogEntry) => {
    setLogs((prev) => {
      const next = [...prev, entry];
      return next.length > MAX_ENTRIES ? next.slice(next.length - MAX_ENTRIES) : next;
    });
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

  // Poll /api/health to track connection state.
  const poll = useCallback(async () => {
    try {
      const res = await fetch(HEALTH_URL);
      if (cancelled.current) return;
      if (res.ok) {
        const body = await res.json();
        setConnStatus("ok");
        // Log the first successful connect as an info entry.
        setLogs((prev) => {
          const lastOk = [...prev].reverse().find((e) => e.message.startsWith("Backend connected"));
          if (!lastOk) {
            const entry: LogEntry = {
              id: mkId(),
              ts: now(),
              level: "info",
              message: `Backend connected — engine: ${body.engine ?? "unknown"}`,
            };
            const next = [...prev, entry];
            return next.length > MAX_ENTRIES ? next.slice(next.length - MAX_ENTRIES) : next;
          }
          return prev;
        });
      } else {
        setConnStatus("error");
      }
    } catch {
      if (cancelled.current) return;
      setConnStatus("error");
    }
    timer.current = setTimeout(poll, POLL_MS);
  }, []);

  useEffect(() => {
    cancelled.current = false;
    void poll();
    return () => {
      cancelled.current = true;
      clearTimeout(timer.current);
    };
  }, [poll]);

  return { connStatus, logs, clearLogs };
}
