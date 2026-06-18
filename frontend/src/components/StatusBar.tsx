import { useEffect, useRef, useState } from "react";
import type { ConnStatus, LogEntry } from "../hooks/useStatusLog";

interface Props {
  connStatus: ConnStatus;
  logs: LogEntry[];
  clearLogs: () => void;
  /** Absolute path to backend.log; undefined until the sidecar starts. */
  logPath: string | null;
}

const STATUS_LABEL: Record<ConnStatus, string> = {
  connecting: "Connecting…",
  ok: "Backend connected",
  error: "Backend unreachable",
};

const LEVEL_ICON: Record<LogEntry["level"], string> = {
  info: "●",
  warn: "▲",
  error: "✕",
};

function fmtTime(d: Date) {
  return d.toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export function StatusBar({ connStatus, logs, clearLogs, logPath }: Props) {
  const [open, setOpen] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const listRef = useRef<HTMLDivElement>(null);
  const prevLen = useRef(logs.length);

  // Open the backend log file in the system's default text editor.
  const openLogFile = () => {
    if (!logPath) return;
    // Use Tauri's opener/shell plugin when inside the desktop app.
    type TauriShellApi = { open(path: string): Promise<void> };
    const shellApi = (window as { __TAURI__?: { shell?: TauriShellApi } }).__TAURI__?.shell;
    if (shellApi) {
      shellApi.open(logPath).catch(console.error);
    }
  };

  // Auto-scroll to bottom when new logs arrive (if autoscroll is on).
  useEffect(() => {
    if (!open || !autoScroll) return;
    if (logs.length !== prevLen.current && listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
    prevLen.current = logs.length;
  }, [logs, open, autoScroll]);

  const handleScroll = () => {
    const el = listRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 24;
    setAutoScroll(atBottom);
  };

  const lastError = [...logs].reverse().find((e) => e.level === "error");

  return (
    <div className={`status-bar${open ? " status-bar--open" : ""}`} role="complementary" aria-label="Status bar">
      {/* Drawer panel */}
      {open && (
        <div className="status-bar__drawer">
          <div className="status-bar__drawer-header">
            <span className="status-bar__drawer-title">API Logs</span>
            <div className="status-bar__drawer-actions">
              {!autoScroll && (
                <button
                  type="button"
                  className="status-bar__action-btn"
                  onClick={() => {
                    setAutoScroll(true);
                    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
                  }}
                  title="Scroll to bottom"
                >
                  ↓ Follow
                </button>
              )}
              {logPath && (
                <button
                  type="button"
                  className="status-bar__action-btn"
                  onClick={openLogFile}
                  title={`Open ${logPath}`}
                >
                  📄 Open log file
                </button>
              )}
              <button
                type="button"
                className="status-bar__action-btn"
                onClick={clearLogs}
                title="Clear logs"
              >
                Clear
              </button>
            </div>
          </div>

          <div
            className="status-bar__log-list"
            ref={listRef}
            onScroll={handleScroll}
            role="log"
            aria-live="polite"
            aria-label="API request log"
          >
            {logs.length === 0 ? (
              <span className="status-bar__log-empty">No log entries yet.</span>
            ) : (
              logs.map((entry) => (
                <div key={entry.id} className={`status-bar__log-row status-bar__log-row--${entry.level}`}>
                  <span className="status-bar__log-icon" aria-hidden="true">
                    {LEVEL_ICON[entry.level]}
                  </span>
                  <span className="status-bar__log-time">{fmtTime(entry.ts)}</span>
                  <span className="status-bar__log-msg">{entry.message}</span>
                  {entry.repeat > 1 && (
                    <span className="status-bar__log-repeat" title={`Repeated ${entry.repeat} times`}>
                      ×{entry.repeat}
                    </span>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Bottom bar strip */}
      <button
        type="button"
        className="status-bar__strip"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls="status-bar-drawer"
        title={open ? "Hide logs" : "Show API logs"}
      >
        {/* Connection indicator */}
        <span className={`status-bar__dot status-bar__dot--${connStatus}`} aria-hidden="true" />
        <span className="status-bar__label">{STATUS_LABEL[connStatus]}</span>

        {/* Show last error inline when drawer is closed */}
        {!open && lastError && connStatus === "error" && (
          <span className="status-bar__inline-error">{lastError.message}</span>
        )}

        {/* Log count badge */}
        {logs.length > 0 && (
          <span className="status-bar__count" aria-label={`${logs.length} log entries`}>
            {logs.length}
          </span>
        )}

        <span className="status-bar__chevron" aria-hidden="true">
          {open ? "▾" : "▴"}
        </span>
      </button>
    </div>
  );
}
