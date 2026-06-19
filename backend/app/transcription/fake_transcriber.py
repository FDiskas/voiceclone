"""A deterministic transcriber for development and tests (no model needed)."""

from __future__ import annotations

from pathlib import Path

from ..cancellation import CancellationToken, raise_if_cancelled


class FakeTranscriber:
    """Returns a fixed placeholder so the app runs without an ASR model."""

    def transcribe(
        self,
        audio_path: Path,
        language: str | None = None,
        cancel: CancellationToken | None = None,
    ) -> str:
        raise_if_cancelled(cancel)
        return "This is an automatically generated placeholder transcript."
