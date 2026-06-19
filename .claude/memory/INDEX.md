# Memory Index

## project/

- [overview](project/overview.md) — registration-free voice-clone web app: React/Vite + FastAPI + OmniVoice, SQLite+files, Tauri desktop later. keywords: goals, stack, scope, omnivoice
- [omnivoice-api](project/omnivoice-api.md) — k2-fsa/OmniVoice real API: zero-shot, generate(text,ref_audio,ref_text), 24kHz, no language arg; streaming=sentence-chunking; whisper auto-transcribe. keywords: omnivoice, tts, api, generate, zero-shot, streaming, whisper
- [dev-environment](project/dev-environment.md) — ALWAYS verify you're inside the dev container before running any command; if not, ask first. Toolchains live in .devcontainer. keywords: devcontainer, environment-check, before-running, confirm, ffmpeg, rust, tauri
- [tauri-backend-lifecycle](project/tauri-backend-lifecycle.md) — Tauri must stop backend on close, and on launch reuse a running backend (via /api/health) or start new. keywords: tauri, backend, lifecycle, spawn, shutdown, single-instance, reuse
- [frontend-conventions](project/frontend-conventions.md) — no router (view-state nav), user prefs in localStorage (default language), shared lists in src/constants. keywords: frontend, react, settings, navigation, localStorage, default-language, preferences

## decisions/

- [stack-choices](decisions/stack-choices.md) — why FastAPI + SQLite + Tauri were chosen over alternatives. keywords: decisions, fastapi, sqlite, tauri, electron
- [frontend-package-manager](decisions/frontend-package-manager.md) — frontend uses pnpm, not npm (npm 11 can't install @tauri-apps/cli). keywords: pnpm, npm, tauri, install
- [monorepo-tooling](decisions/monorepo-tooling.md) — pnpm workspace (root coordinator + frontend = only JS pkg); Turborepo rejected; backend Python launched via root scripts + concurrently. keywords: monorepo, pnpm, workspace, turborepo, root, dev-launcher
- [mps-memory-synthesis](decisions/mps-memory-synthesis.md) — synthesis OOM crashed macOS; fixed via float16-on-mps, empty_cache between sentences, serialized generation, 0.8 MPS watermark cap. keywords: mps, oom, crash, float16, synthesis, apple-silicon, performance
- [ffmpeg-not-avconv](decisions/ffmpeg-not-avconv.md) — NO system ffmpeg dep: WebView decodes to PCM wav (convertToWav), backend reads via soundfile + torchaudio resample, faster-whisper uses PyAV. Never reintroduce ffmpeg/pydub/avconv. keywords: ffmpeg, avconv, pydub, soundfile, pyav, webaudio, convertToWav
- [model-management](decisions/model-management.md) — ManagedModel capability (voice+whisper), opt-in download via button, /api/models endpoints, HF cache helper, byte-level progress. keywords: models, delete, download, warmup, huggingface, cache, registry, settings, progress
- [macos-unsigned-quarantine](decisions/macos-unsigned-quarantine.md) — app ships UNSIGNED; quarantine can't be stripped in CI (added client-side on download); users run xattr or "Open Anyway". keywords: macos, codesign, notarization, quarantine, gatekeeper, xattr, unsigned
- [release-versioning](decisions/release-versioning.md) — single version source is frontend/package.json; tauri.conf.json version → ../package.json, so `pnpm version patch` drives built app version + git tag. keywords: version, release, pnpm, tauri, git-tag, bump
- [tauri-packaging-gotchas](decisions/tauri-packaging-gotchas.md) — backend data dir must come from Tauri app_data_dir (onefile __file__ is ephemeral → 404/no persistence); downloads need native save (WKWebView ignores <a download>). keywords: tauri, pyinstaller, onefile, data_dir, persistence, 404, download, wkwebview, save

## developer/

- [profile](developer/profile.md) — vytenis.kuciauskas@nfq.com; values SOLID/clean code (invoked /solid). keywords: role, preferences, solid
