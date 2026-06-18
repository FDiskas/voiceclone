"""Whisper ASR adapter, backed by faster-whisper.

The model loads lazily on first use so the server starts instantly and only
pays the download/load cost when a transcription is actually requested.
"""

from __future__ import annotations

import logging
from pathlib import Path

_logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """Wraps `faster_whisper.WhisperModel` behind the Transcriber protocol."""

    def __init__(self, model_size: str, device: str, compute_type: str) -> None:
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model = None

    def _load(self):
        if self._model is not None:
            return self._model
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "faster-whisper is not installed. Run `pip install faster-whisper` "
                "or set VOICECLONE_TRANSCRIBER=fake."
            ) from exc

        _logger.info("Loading Whisper model %s on %s", self._model_size, self._device)
        self._model = WhisperModel(
            self._model_size, device=self._device, compute_type=self._compute_type
        )
        return self._model

    def transcribe(self, audio_path: Path, language: str | None = None) -> str:
        model = self._load()
        segments, _ = model.transcribe(str(audio_path), language=language)
        return " ".join(segment.text.strip() for segment in segments).strip()
