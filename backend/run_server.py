"""Entry point for the bundled desktop sidecar.

Runs the FastAPI app with uvicorn on a fixed local port. Packaged into a
single binary with PyInstaller (see build_sidecar.sh) and launched by Tauri.
"""

from __future__ import annotations

import os
import threading
import time

import uvicorn

from app.main import app


def _pid_alive(pid: int) -> bool:
    """True if a process with `pid` currently exists."""
    if os.name == "nt":  # Windows
        import ctypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid
        )
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, just not ours to signal
    return True


def _install_parent_watchdog(poll_seconds: float = 0.75) -> None:
    """Exit when the launching process (Tauri) goes away.

    PyInstaller's --onefile bootloader spawns this server as a child, so when
    Tauri kills the bootloader we get reparented to init/launchd and would
    otherwise linger as an orphan. Tauri passes its own PID via
    VOICECLONE_PARENT_PID; we watch that specific PID rather than relying on
    PPID, which reparenting clobbers. Absent the var (dev/manual runs) we skip
    the watchdog entirely so a normally-launched server is never killed.
    """
    raw = os.environ.get("VOICECLONE_PARENT_PID")
    if not raw:
        return
    try:
        parent_pid = int(raw)
    except ValueError:
        return

    def _watch() -> None:
        while True:
            if not _pid_alive(parent_pid):
                os._exit(0)
            time.sleep(poll_seconds)

    threading.Thread(target=_watch, name="parent-watchdog", daemon=True).start()


def main() -> None:
    _install_parent_watchdog()
    host = os.environ.get("VOICECLONE_HOST", "127.0.0.1")
    port = int(os.environ.get("VOICECLONE_PORT", "8000"))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
