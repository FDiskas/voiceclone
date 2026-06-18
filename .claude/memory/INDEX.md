# Memory Index

## project/

- [overview](project/overview.md) — registration-free voice-clone web app: React/Vite + FastAPI + OmniVoice, SQLite+files, Tauri desktop later. keywords: goals, stack, scope, omnivoice
- [omnivoice-api](project/omnivoice-api.md) — k2-fsa/OmniVoice real API: zero-shot, generate(text,ref_audio,ref_text), 24kHz, no language arg; streaming=sentence-chunking; whisper auto-transcribe. keywords: omnivoice, tts, api, generate, zero-shot, streaming, whisper
- [dev-environment](project/dev-environment.md) — ALWAYS verify you're inside the dev container before running any command; if not, ask first. Toolchains live in .devcontainer. keywords: devcontainer, environment-check, before-running, confirm, ffmpeg, rust, tauri
- [tauri-backend-lifecycle](project/tauri-backend-lifecycle.md) — Tauri must stop backend on close, and on launch reuse a running backend (via /api/health) or start new. keywords: tauri, backend, lifecycle, spawn, shutdown, single-instance, reuse

## decisions/

- [stack-choices](decisions/stack-choices.md) — why FastAPI + SQLite + Tauri were chosen over alternatives. keywords: decisions, fastapi, sqlite, tauri, electron
- [frontend-package-manager](decisions/frontend-package-manager.md) — frontend uses pnpm, not npm (npm 11 can't install @tauri-apps/cli). keywords: pnpm, npm, tauri, install
- [mps-memory-synthesis](decisions/mps-memory-synthesis.md) — synthesis OOM crashed macOS; fixed via float16-on-mps, empty_cache between sentences, serialized generation, 0.8 MPS watermark cap. keywords: mps, oom, crash, float16, synthesis, apple-silicon, performance
- [ffmpeg-not-avconv](decisions/ffmpeg-not-avconv.md) — NO system ffmpeg dep: WebView decodes to PCM wav (convertToWav), backend reads via soundfile + torchaudio resample, faster-whisper uses PyAV. Never reintroduce ffmpeg/pydub/avconv. keywords: ffmpeg, avconv, pydub, soundfile, pyav, webaudio, convertToWav
- [macos-unsigned-quarantine](decisions/macos-unsigned-quarantine.md) — app ships UNSIGNED; quarantine can't be stripped in CI (added client-side on download); users run xattr or "Open Anyway". keywords: macos, codesign, notarization, quarantine, gatekeeper, xattr, unsigned
- [tauri-packaging-gotchas](decisions/tauri-packaging-gotchas.md) — backend data dir must come from Tauri app_data_dir (onefile __file__ is ephemeral → 404/no persistence); downloads need native save (WKWebView ignores <a download>). keywords: tauri, pyinstaller, onefile, data_dir, persistence, 404, download, wkwebview, save

## developer/

- [profile](developer/profile.md) — vytenis.kuciauskas@nfq.com; values SOLID/clean code (invoked /solid). keywords: role, preferences, solid
