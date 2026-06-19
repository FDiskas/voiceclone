"""Whisper ASR adapter, backed by faster-whisper.

The model loads lazily on first use so the server starts instantly and only
pays the download/load cost when a transcription is actually requested.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ..cancellation import CancellationToken, raise_if_cancelled
from ..models import huggingface_cache
from ..models.managed_model import DeletedModel, ModelInfo

_logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """Wraps `faster_whisper.WhisperModel` behind the Transcriber protocol."""

    model_key = "transcription"

    def __init__(self, model_size: str, device: str, compute_type: str) -> None:
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model = None

    @property
    def _repo_id(self) -> str:
        """The Hugging Face repo faster-whisper downloads weights from.

        A size name ("base", "small", …) maps to the Systran CT2 conversion;
        a value containing "/" is already a repo id (or local path) and is used
        verbatim — mirroring faster-whisper's own resolution.
        """
        if "/" in self._model_size:
            return self._model_size
        return f"Systran/faster-whisper-{self._model_size}"

    # --- ManagedModel ---------------------------------------------------

    def model_info(self) -> ModelInfo:
        entry = huggingface_cache.describe(self._repo_id)
        return ModelInfo(
            key=self.model_key,
            label="Transcription model",
            repo_id=self._repo_id,
            downloaded=entry.downloaded,
            path=entry.path,
            size_bytes=entry.size_bytes,
        )

    def delete_model(self) -> DeletedModel:
        """Drop the in-memory model and purge its weights from the cache."""
        self._model = None
        found, freed = huggingface_cache.purge(self._repo_id)
        _logger.info(
            "Deleted Whisper model %s (found=%s, freed=%d bytes)",
            self._repo_id,
            found,
            freed,
        )
        return DeletedModel(
            key=self.model_key, repo_id=self._repo_id, found=found, freed_bytes=freed
        )

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

    def transcribe(
        self,
        audio_path: Path,
        language: str | None = None,
        cancel: CancellationToken | None = None,
    ) -> str:
        model = self._load()
        # faster-whisper decodes lazily as `segments` is iterated, so this loop
        # is where the work actually happens — and the place to honour a cancel.
        segments, _ = model.transcribe(str(audio_path), language=language)
        parts: list[str] = []
        for segment in segments:
            raise_if_cancelled(cancel)
            parts.append(segment.text.strip())
        return " ".join(parts).strip()
