---
name: tauri-packaging-gotchas
description: Packaged-app gotchas — backend data dir must come from Tauri app_data_dir (PyInstaller onefile __file__ is ephemeral); downloads need native save (WKWebView ignores <a download>).
keywords: tauri, pyinstaller, onefile, data_dir, persistence, 404, download, wkwebview, save dialog, sidecar, app_data_dir
created: 2026-06-19
updated: 2026-06-19
---

**Gotcha 1 — backend data dir must be injected by Tauri.**
The backend's `data_dir` defaults to `Path(__file__).resolve().parent.parent / "data"` (config.py). In the PyInstaller `--onefile` sidecar, `__file__` lives in the ephemeral `_MEIxxxx` extraction dir that is recreated every launch and deleted on exit. Result: SQLite DB + reference `.wav` files are wiped each restart, and absolute `reference_audio_path` rows go stale → `GET /api/profiles/{id}/audio` returns 404 and nothing persists.

**Fix applied:** Tauri's `try_spawn_backend` (src-tauri/src/main.rs) passes `VOICECLONE_DATA_DIR = app.path().app_data_dir()` to the sidecar. The backend already honors it via pydantic's `VOICECLONE_` env prefix (Settings.data_dir). Always inject a stable per-user dir for any sidecar that persists state — never rely on the default.

**Gotcha 2 — downloads need a native save in the desktop shell.**
WKWebView (Tauri on macOS) silently ignores programmatic `<a download>` clicks, so the old `triggerDownload` did nothing in the packaged app (affected generated-speech AND profile-audio downloads).

**Fix applied:** `saveBlob()` in src/api/audio.ts detects Tauri via `__TAURI_INTERNALS__`, opens `@tauri-apps/plugin-dialog` `save()`, and writes bytes through a custom Rust `save_file` command (std::fs — avoids fs-plugin scope config). Falls back to the anchor click in a plain browser. Requires `tauri-plugin-dialog` (Cargo), `@tauri-apps/api` + `@tauri-apps/plugin-dialog` (npm), and `dialog:allow-save` in capabilities/default.json.

Related: [[tauri-backend-lifecycle]], [[ffmpeg-not-avconv]]
