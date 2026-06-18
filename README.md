# VoiceClone

Registration-free voice cloning. Record or upload a voice + transcript, create a
profile, then type any text and hear it spoken in that cloned voice.

Powered by [k2-fsa/OmniVoice](https://github.com/k2-fsa/OmniVoice) — a zero-shot
multilingual TTS model.

```
voiceclone/
├── backend/    FastAPI + OmniVoice (Python)
└── frontend/   React + Vite (TypeScript)
```

## How it works

OmniVoice is **zero-shot**: there is no per-voice training step. A "profile" is
just the stored reference audio + its transcript + a language label. Every
synthesis call re-clones the voice from that reference. Language is metadata only
— OmniVoice infers the spoken language from the text you type.

The voice engine sits behind a `VoiceEngine` interface ([backend/app/engine/base.py](backend/app/engine/base.py)).
Two implementations exist:

- **`fake`** (default) — emits a sine tone. Runs the whole app with no model
  download or GPU. Used by the tests and ideal for UI development.
- **`omnivoice`** — the real model.

Swap via the `VOICECLONE_ENGINE` env var. Nothing else changes.

### Streaming synthesis

OmniVoice's `generate()` returns complete audio, so "streaming" here means
**sentence-level chunking** (the same approach the community OpenAI server
uses). The backend splits text into sentences, synthesizes each, and streams
them as they finish — the first sentence plays while the rest render. Wire
format: repeated `[uint32 big-endian length][wav bytes]`; the frontend decodes
each chunk and schedules them gaplessly via the Web Audio API.

### Auto-transcription (Whisper)

A profile's transcript is optional. If left blank, the backend transcribes the
reference audio with Whisper (`faster-whisper`) to fill it. The frontend also
exposes an **Auto-transcribe** button (via `POST /api/transcribe`) so you can
review/edit the text before creating the profile. Like the engine, the
transcriber sits behind a `Transcriber` interface with a `fake` default and a
`whisper` implementation, selected by `VOICECLONE_TRANSCRIBER`.

## Prerequisites

- Python ≥ 3.10
- Node ≥ 18 and [pnpm](https://pnpm.io/) (`corepack enable pnpm`)
- [`ffmpeg`](https://ffmpeg.org/) on your `PATH` (used to normalize uploaded /
  recorded audio to 24 kHz mono wav)
- For the desktop build only: [Rust](https://rustup.rs/) and PyInstaller

## Backend

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # add ".[omnivoice]" for the real model

cp .env.example .env             # defaults to the fake engine
uvicorn app.main:app --reload    # http://127.0.0.1:8000  (docs at /docs)
```

Run the tests:

```bash
pytest
```

### Using the real OmniVoice model

```bash
pip install -e ".[omnivoice]"    # installs omnivoice + torch
# in .env:
VOICECLONE_ENGINE=omnivoice
VOICECLONE_DEVICE=auto           # cuda:0 / mps / cpu — auto-detected
```

The model weights download from Hugging Face on first run. On a Mac the
engine runs on `mps`/`cpu` (float32); CUDA uses float16.

The backend warms the model up at startup and reports progress via
`GET /api/engine/status`, so the UI can show a download/load indicator on
first launch instead of hanging on the first synthesis. The `fake` engine
reports `ready` immediately, so the indicator never appears in dev.

### Enabling Whisper transcription

```bash
pip install -e ".[whisper]"      # installs faster-whisper
# in .env:
VOICECLONE_TRANSCRIBER=whisper
VOICECLONE_WHISPER_MODEL_SIZE=base   # tiny … large-v3
```

## Frontend

```bash
cd frontend
pnpm install
pnpm dev                         # http://localhost:5173
```

The dev server proxies `/api` to the backend on port 8000, so start the backend
first. To point at a different backend, set `VITE_API_BASE` (see `.env.example`).

## Data

SQLite metadata and reference audio live under `backend/data/` (configurable via
`VOICECLONE_DATA_DIR`). Delete that folder to wipe all profiles.

## Desktop app (Tauri)

The app ships as a [Tauri 2](https://tauri.app/) desktop bundle: the Vite build
is the webview, and the FastAPI backend is launched as a **sidecar** binary.
The Rust shell ([frontend/src-tauri/src/main.rs](frontend/src-tauri/src/main.rs))
spawns the backend on startup and kills it on exit. The frontend auto-detects
the Tauri runtime and targets the sidecar at `http://127.0.0.1:8000`.

One-time setup:

```bash
# 1. Rust toolchain
curl https://sh.rustup.rs -sSf | sh

# 2. App icons (needs a square PNG)
cd frontend && pnpm exec tauri icon path/to/logo.png
```

Build:

```bash
# 1. Bundle the Python backend into the sidecar binary
cd backend
pip install pyinstaller
./build_sidecar.sh        # -> frontend/src-tauri/binaries/voiceclone-backend-<triple>

# 2. Build (or run) the desktop app
cd ../frontend
pnpm desktop:build        # production bundle for your OS
# or
pnpm desktop:dev          # live dev with the sidecar
```

Mac/Windows/Linux from one codebase. For an offline app, build the sidecar with
the `omnivoice` (and optionally `whisper`) extras installed so the model loads
locally — note the weights still download from Hugging Face on first run unless
pre-cached. The desktop shell spawns the sidecar with `VOICECLONE_ENGINE=omnivoice`
and `VOICECLONE_TRANSCRIBER=whisper` by default; export either var before
launching `tauri dev` to override (e.g. `VOICECLONE_ENGINE=fake`).

### Releasing (GitHub Actions)

[.github/workflows/release.yml](.github/workflows/release.yml) builds installers
for macOS (Apple Silicon + Intel), Linux, and Windows and attaches them to a
**draft** GitHub Release. Each runner bundles the real OmniVoice + Whisper deps
into the sidecar, then `tauri-action` builds the bundle.

```bash
git tag v0.1.0 && git push origin v0.1.0   # or run the workflow manually
```

A placeholder icon set is committed under `frontend/src-tauri/icons/`; replace
it with a real square logo via `pnpm tauri icon path/to/logo.png`. The ML deps
make the build heavy (multi-GB installers, longer builds).

## Architecture notes

- **Domain** (`backend/app/domain`) — entities + value objects; invalid values
  can't be constructed.
- **Engine** (`backend/app/engine`) — the `VoiceEngine` abstraction + adapters.
- **Storage** (`backend/app/storage`) — SQLite repository, audio on disk.
- **Services** (`backend/app/services`) — `ProfileService`, `SynthesisService`
  orchestrate use cases against abstractions, not concretions.
- **API** (`backend/app/api`) — thin FastAPI routers; the composition root in
  `dependencies.py` is the only place that wires concretes together.

## API

| Method | Path | Purpose |
| ------ | ---- | ------- |
| `GET`  | `/api/health` | Liveness + active engine |
| `GET`  | `/api/engine/status` | Engine readiness: `state` (idle/downloading/loading/ready/error), `message`, `progress` (0–1 or null), `detail` |
| `POST` | `/api/engine/warmup` | Begin loading the model now (idempotent); returns the current status |
| `DELETE` | `/api/engine/model` | Delete the downloaded model (reclaim disk; re-downloads when next needed) |
| `GET`  | `/api/profiles` | List profiles |
| `POST` | `/api/profiles` | Create profile (multipart: name, language, audio, optional transcript) |
| `DELETE` | `/api/profiles/{id}` | Delete a profile |
| `POST` | `/api/profiles/{id}/speech` | Synthesize text → `audio/wav` (json: text, speed) |
| `POST` | `/api/profiles/{id}/speech/stream` | Stream sentence chunks → length-prefixed wav frames |
| `POST` | `/api/transcribe` | Transcribe a clip → `{ text }` (multipart: audio, optional language) |
