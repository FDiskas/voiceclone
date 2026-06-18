# Memory Index

## project/

- [overview](project/overview.md) — registration-free voice-clone web app: React/Vite + FastAPI + OmniVoice, SQLite+files, Tauri desktop later. keywords: goals, stack, scope, omnivoice
- [omnivoice-api](project/omnivoice-api.md) — k2-fsa/OmniVoice real API: zero-shot, generate(text,ref_audio,ref_text), 24kHz, no language arg; streaming=sentence-chunking; whisper auto-transcribe. keywords: omnivoice, tts, api, generate, zero-shot, streaming, whisper
- [dev-environment](project/dev-environment.md) — ALWAYS verify you're inside the dev container before running any command; if not, ask first. Toolchains live in .devcontainer. keywords: devcontainer, environment-check, before-running, confirm, ffmpeg, rust, tauri

## decisions/

- [stack-choices](decisions/stack-choices.md) — why FastAPI + SQLite + Tauri were chosen over alternatives. keywords: decisions, fastapi, sqlite, tauri, electron
- [frontend-package-manager](decisions/frontend-package-manager.md) — frontend uses pnpm, not npm (npm 11 can't install @tauri-apps/cli). keywords: pnpm, npm, tauri, install

## developer/

- [profile](developer/profile.md) — vytenis.kuciauskas@nfq.com; values SOLID/clean code (invoked /solid). keywords: role, preferences, solid
