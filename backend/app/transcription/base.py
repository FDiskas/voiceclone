"""The Transcriber abstraction (Dependency Inversion boundary).

Lets the app auto-fill a reference transcript from audio without binding the
services to any particular ASR library. Whisper is one adapter; the fake is
another.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class Transcriber(Protocol):
    """Produces text from a spoken-audio file."""

    def transcribe(self, audio_path: Path, language: str | None = None) -> str:
        ...
