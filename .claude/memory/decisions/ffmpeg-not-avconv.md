---
name: ffmpeg-not-avconv
description: Decision — voiceclone has NO system ffmpeg dependency. WebView decodes audio to PCM wav before upload; backend reads via soundfile (libsndfile) + torchaudio resample; faster-whisper uses bundled PyAV. Never reintroduce ffmpeg/pydub/avconv.
keywords: [ffmpeg, avconv, pydub, libav, soundfile, libsndfile, pyav, faster-whisper, webaudio, convertToWav, audio, PATH]
created: 2026-06-18
updated: 2026-06-18
---

**Decision (2026-06-18):** voiceclone does **not** depend on a system `ffmpeg` binary. We removed it after the macOS GUI-launch PATH problem (Finder/Dock apps get a minimal PATH without Homebrew's `/opt/homebrew/bin`, so the spawned backend couldn't find ffmpeg). Modeled on jamiepine/voicebox.

**Architecture (how audio is normalized without ffmpeg):**

1. **Frontend** ([frontend/src/api/audio.ts](frontend/src/api/audio.ts)) — `convertToWav` / `toUploadAudio` decode any recording/upload via the WebView's Web Audio API (`decodeAudioData` + `OfflineAudioContext` → 24 kHz mono 16-bit PCM wav). Wired into `createProfile` + `transcribe` in [frontend/src/api/client.ts](frontend/src/api/client.ts). Falls back to sending original bytes if decode fails.
2. **Backend** ([backend/app/audio/converter.py](backend/app/audio/converter.py)) — `normalize_to_wav` reads with `soundfile` (libsndfile bundled in the wheel — no system binary; also decodes wav/flac/ogg/mp3), downmixes to mono, resamples to 24 kHz via `torchaudio.functional.resample` (existing dep). No subprocess.
3. **Transcription** — `faster-whisper` decodes via bundled **PyAV**, not a system ffmpeg.

**Why never avconv:** `avconv` is the dead libav fork (abandoned ~2018). It was never the answer; the warning just meant no decoder on PATH.

**How to apply:**
- Do NOT add `ffmpeg` shell-outs, `pydub`, or a PATH-augmentation hack to the Tauri spawn ([frontend/src-tauri/src/main.rs](frontend/src-tauri/src/main.rs)) — that hack was added then removed.
- The leftover `pydub` RuntimeWarning in logs is a transitive dep's import-time noise, not our code — harmless.
- Only ever feed the engine 24 kHz mono PCM wav. See [[tauri-backend-lifecycle]], [[dev-environment]].
