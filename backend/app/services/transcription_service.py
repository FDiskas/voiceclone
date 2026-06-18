"""Use case: transcribe an uploaded/recorded clip into reference text."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Callable

from ..audio.converter import normalize_to_wav
from ..transcription.base import Transcriber

AudioNormalizer = Callable[[Path, Path], Path]


class TranscriptionService:
    """Normalizes arbitrary audio to wav, then runs the Transcriber on it."""

    def __init__(self, transcriber: Transcriber, normalize: AudioNormalizer = normalize_to_wav) -> None:
        self._transcriber = transcriber
        self._normalize = normalize

    def transcribe(
        self, audio_bytes: bytes, original_filename: str, language: str | None = None
    ) -> str:
        suffix = Path(original_filename).suffix or ".bin"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as raw:
            raw.write(audio_bytes)
            raw_path = Path(raw.name)
        wav_path = raw_path.with_suffix(".wav")
        try:
            self._normalize(raw_path, wav_path)
            return self._transcriber.transcribe(wav_path, language)
        finally:
            raw_path.unlink(missing_ok=True)
            wav_path.unlink(missing_ok=True)
