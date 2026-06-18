---
name: stack-choices
description: why FastAPI + SQLite + Tauri were chosen over alternatives for voiceclone
keywords: [decisions, fastapi, sqlite, tauri, electron, node]
created: 2026-06-18
updated: 2026-06-18
---

**Decision:** FastAPI (Python) backend, SQLite+files persistence, Tauri for the eventual desktop app.

**Why:**

- FastAPI: OmniVoice is a Python model — calling it in-process avoids IPC/subprocess overhead vs a Node backend shelling out to Python. See [[omnivoice-api]].
- SQLite + files: survives restarts, zero infra setup, and ports cleanly into the offline desktop app. In-memory was rejected (users would lose profiles on restart).
- Tauri over Electron: tiny binaries, bundles the Vite React build, ships the Python backend as a sidecar; smaller download than Electron's Chromium+Node.

**How to apply:** Keep the React frontend talking to the backend purely over HTTP (configurable base URL) so the same frontend works in browser dev and inside Tauri.
