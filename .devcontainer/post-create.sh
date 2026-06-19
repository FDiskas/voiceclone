#!/usr/bin/env bash
# Runs once after the dev container is created. Installs project dependencies
# for both the backend and frontend. Heavy ML extras (omnivoice/whisper) and the
# desktop sidecar are left as opt-in steps to keep first-create time reasonable.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Enabling pnpm via corepack"
corepack enable pnpm

echo "==> Backend: virtualenv + dependencies"
python -m venv backend/.venv
backend/.venv/bin/pip install --upgrade pip
backend/.venv/bin/pip install -e "./backend[dev]"
backend/.venv/bin/pip install -e "./backend[dev]"

echo "==> Frontend: pnpm install"
(cd frontend && pnpm install)

cat <<'EOF'

Dev container ready.

  Backend:   cd backend && .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0
  Frontend:  cd frontend && pnpm dev --host

Optional, when you want the real model / desktop build:
  Real TTS:        backend/.venv/bin/pip install -e "./backend[omnivoice]"  (set VOICECLONE_ENGINE=omnivoice)
  Whisper:         backend/.venv/bin/pip install -e "./backend[whisper]"    (set VOICECLONE_TRANSCRIBER=whisper)
  Desktop sidecar: backend/.venv/bin/pip install pyinstaller && (cd backend && ./build_sidecar.sh)
  Desktop dev:     cd frontend && pnpm desktop:dev      (Linux GUI; needs X11 forwarding to show a window)
EOF
