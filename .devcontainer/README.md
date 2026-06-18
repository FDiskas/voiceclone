# Dev container

A Linux dev environment that holds every toolchain off your host disk: Python
3.12, Node 20 + pnpm, the Rust/Tauri toolchain, the Tauri 2 system libraries,
and a working `ffmpeg`.

## Use it

Open the repo in VS Code → **Reopen in Container** (Dev Containers extension),
or `devcontainer up --workspace-folder .` with the CLI. On first create,
[post-create.sh](post-create.sh) sets up the backend venv and runs
`pnpm install`.

Then:

```bash
# backend (bind to 0.0.0.0 so the forwarded port works)
cd backend && .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0

# frontend
cd frontend && pnpm dev --host
```

Ports **8000** (backend) and **5173** (frontend) are forwarded to your host —
the web app is fully usable in a browser this way.

## What works where

| Task | In this container |
| ---- | ----------------- |
| Backend + frontend dev (browser) | ✅ full |
| Backend tests (`pytest`) | ✅ full |
| Compile Tauri / build the **Linux** bundle (`.deb`/AppImage) | ✅ |
| Show the Tauri **GUI window** | ⚠️ needs X11 forwarding (e.g. XQuartz on macOS) |
| Build a macOS `.app` / Windows `.exe` | ❌ must build on that OS (no cross-compile) |

The container exists to move heavy toolchains off the host and to provide a
working `ffmpeg`/Rust setup; final mac/Windows desktop bundles are still built
on their native OS.
