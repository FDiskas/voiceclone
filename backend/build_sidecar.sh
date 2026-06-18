#!/usr/bin/env bash
# Build the FastAPI backend into a single binary and place it where Tauri
# expects the sidecar (frontend/src-tauri/binaries/voiceclone-backend-<triple>).
#
# Usage:  ./build_sidecar.sh            # builds with the current venv
# Requires: PyInstaller (pip install pyinstaller) and the backend deps.
set -euo pipefail

cd "$(dirname "$0")"

# Tauri names sidecars with the Rust host target triple. CI sets TRIPLE
# explicitly (per matrix target); locally we derive it from rustc, falling
# back to a guess from uname.
if [ -z "${TRIPLE:-}" ]; then
  if command -v rustc >/dev/null 2>&1; then
    TRIPLE="$(rustc -Vv | sed -n 's/^host: //p')"
  else
    echo "warning: rustc not found; guessing target triple from uname" >&2
    case "$(uname -s)-$(uname -m)" in
      Darwin-arm64) TRIPLE="aarch64-apple-darwin" ;;
      Darwin-x86_64) TRIPLE="x86_64-apple-darwin" ;;
      Linux-x86_64) TRIPLE="x86_64-unknown-linux-gnu" ;;
      Linux-aarch64) TRIPLE="aarch64-unknown-linux-gnu" ;;
      MINGW*-x86_64 | MSYS*-x86_64 | CYGWIN*-x86_64) TRIPLE="x86_64-pc-windows-msvc" ;;
      *) echo "error: unknown platform; set TRIPLE manually" >&2; exit 1 ;;
    esac
  fi
fi

OUT_DIR="../frontend/src-tauri/binaries"
mkdir -p "$OUT_DIR"

# Heavy ML deps (torch, omnivoice, faster-whisper) need their data files and
# dynamic libraries pulled in explicitly. CI sets EXTRA_COLLECT to a
# space-separated package list when bundling the real engine; it's empty for a
# fake-engine build.
COLLECT_ARGS=()
for pkg in ${EXTRA_COLLECT:-}; do
  COLLECT_ARGS+=(--collect-all "$pkg")
done

echo "Building sidecar for $TRIPLE … (extra collect: ${EXTRA_COLLECT:-none})"
pyinstaller --noconfirm --onefile --name voiceclone-backend \
  --collect-all app \
  ${COLLECT_ARGS[@]+"${COLLECT_ARGS[@]}"} \
  run_server.py

# PyInstaller appends .exe on Windows; mirror that suffix on the sidecar name.
if [ -f "dist/voiceclone-backend.exe" ]; then
  cp "dist/voiceclone-backend.exe" "$OUT_DIR/voiceclone-backend-$TRIPLE.exe"
  echo "Wrote $OUT_DIR/voiceclone-backend-$TRIPLE.exe"
else
  cp "dist/voiceclone-backend" "$OUT_DIR/voiceclone-backend-$TRIPLE"
  echo "Wrote $OUT_DIR/voiceclone-backend-$TRIPLE"
fi
