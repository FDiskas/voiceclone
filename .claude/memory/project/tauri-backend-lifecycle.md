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

**How to apply:**
- Detect "already running" via the existing `GET /api/health` endpoint (returns 200) on the expected port before spawning.
- Tie backend shutdown to Tauri exit (e.g. kill the child on window/app close + a process-exit guard). A Rust-managed child process is killed when dropped, but app-close handlers / sidecar config must ensure the spawn is actually torn down.
- Relates to spawn/error handling already added in StatusBar/loading-screen work; see [[dev-environment]].
