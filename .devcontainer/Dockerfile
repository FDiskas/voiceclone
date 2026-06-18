# Dev container for VoiceClone: backend (FastAPI), frontend (Vite/pnpm) and the
# Tauri 2 desktop toolchain. Language runtimes (Python, Node, Rust) come from
# dev container "features"; this image adds the system libraries Tauri 2 needs
# on Linux plus a working ffmpeg for audio normalization/transcription.
FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

RUN apt-get update \
 && export DEBIAN_FRONTEND=noninteractive \
 && apt-get install -y --no-install-recommends \
    # --- Tauri 2 (webkitgtk 4.1 / libsoup3) ---
    libwebkit2gtk-4.1-dev \
    libjavascriptcoregtk-4.1-dev \
    libsoup-3.0-dev \
    libgtk-3-dev \
    librsvg2-dev \
    libayatana-appindicator3-dev \
    libxdo-dev \
    libssl-dev \
    pkg-config \
    build-essential \
    curl wget file \
    # --- audio (uploads/recordings -> 24 kHz mono wav) ---
    ffmpeg \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
