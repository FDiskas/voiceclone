---
name: tauri-backend-lifecycle
description: Requirement — Tauri app must stop the backend on close, and on launch reuse an already-running backend or start a new one (single-instance)
keywords: [tauri, backend, lifecycle, spawn, shutdown, health, single-instance, port, reuse]
created: 2026-06-18
updated: 2026-06-18
---

**Requirement:** The Tauri desktop app owns the backend process lifecycle:

1. **On close:** when the Tauri app exits, it must also stop the backend (no orphaned FastAPI/uvicorn process left running).
2. **On launch:** detect whether a backend is already running — if so, reuse it; otherwise start a new one. Don't blindly spawn a duplicate on the same port.

**Why:** User reported orphaned/duplicate backends and wants clean single-instance behavior.

**On-close STATUS (done 2026-06-18):** the orphan was caused by PyInstaller `--onefile`: Tauri holds the *bootloader* PID, but the bootloader spawns the real uvicorn server as a child; killing the bootloader reparented the server to launchd (PID 1) → orphan. Fix: Tauri passes its own PID as `VOICECLONE_PARENT_PID` ([frontend/src-tauri/src/main.rs](frontend/src-tauri/src/main.rs)); the backend runs a daemon watchdog ([backend/run_server.py](backend/run_server.py)) that `os._exit`s when that PID dies. Watches the Tauri PID (not PPID, which reparenting clobbers); skipped when the env var is absent so dev/manual runs aren't killed. `kill_backend` on Destroyed/ExitRequested still kills the bootloader for promptness.

**On-launch STATUS (done 2026-06-18):** reuse-or-spawn implemented in [frontend/src-tauri/src/main.rs](frontend/src-tauri/src/main.rs). `backend_already_running()` does a dependency-free raw-TCP `GET /api/health` probe on `VOICECLONE_HOST:VOICECLONE_PORT` (default 127.0.0.1:8000) in `setup()`; if a 200 comes back it reuses (returns early, spawns nothing). A reused backend is NOT owned, so `kill_backend` leaves it alone on exit. Closed port → ConnectionRefused returns instantly, so no startup delay in the normal spawn case.

**How to apply:**
- Don't reintroduce a process-group kill from Rust — same group as the Tauri app, would kill the app too. The PID-watchdog is the chosen mechanism.
- Windows note: `_pid_alive` uses OpenProcess; watchdog is cross-platform.
- Relates to spawn/error handling in StatusBar/loading-screen work; see [[dev-environment]], [[ffmpeg-not-avconv]].
