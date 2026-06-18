"""Normalizes any uploaded/recorded audio into the wav OmniVoice expects.

Browsers record webm/opus, users upload mp3/m4a/etc. We funnel everything
through ffmpeg into a 24 kHz mono PCM wav so the engine receives one shape.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..domain.errors import AudioConversionError

_TARGET_SAMPLE_RATE = 24_000


def normalize_to_wav(source: Path, destination: Path) -> Path:
    """Convert `source` audio into a mono 24 kHz wav at `destination`."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise AudioConversionError(
            "ffmpeg is required to process audio but was not found on PATH."
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        "-y",
        "-i",
        str(source),
        "-ac",
        "1",
        "-ar",
        str(_TARGET_SAMPLE_RATE),
        "-f",
        "wav",
        str(destination),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise AudioConversionError(
            f"ffmpeg could not decode the audio: {result.stderr.strip().splitlines()[-1:] or 'unknown error'}"
        )
    return destination
