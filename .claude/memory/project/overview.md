---
name: overview
description: registration-free voice-clone web app — React/Vite + FastAPI + OmniVoice, SQLite+files, Tauri desktop later
keywords: [goals, stack, scope, omnivoice, voiceclone]
created: 2026-06-18
updated: 2026-06-18
---

**What we're building:** A web app where an anonymous user (no registration) can upload OR record their voice, provide a transcript, pick a language, and create a reusable "voice profile". Then they select a profile, type new text, and hear it spoken in the cloned voice.

**Stack (user-chosen):**

- Frontend: React + Vite (TypeScript). Later wrapped as a Tauri desktop app (Mac/Win/Linux).
- Backend: Python FastAPI, calling OmniVoice as a local in-process model.
- Persistence: SQLite for profile metadata + audio files on disk. See [[omnivoice-api]].

**Key constraint:** No auth/registration. Profiles are anonymous, identified by generated id. Build front+back cleanly so the Tauri desktop wrapper drops in later (Python backend shipped as a sidecar).
