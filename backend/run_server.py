"""Entry point for the bundled desktop sidecar.

Runs the FastAPI app with uvicorn on a fixed local port. Packaged into a
single binary with PyInstaller (see build_sidecar.sh) and launched by Tauri.
"""

from __future__ import annotations

import os

import uvicorn

from app.main import app


def main() -> None:
    host = os.environ.get("VOICECLONE_HOST", "127.0.0.1")
    port = int(os.environ.get("VOICECLONE_PORT", "8000"))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
