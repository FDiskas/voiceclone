"""Normalizes any uploaded/recorded audio into the wav OmniVoice expects.

The WebView converts recordings/uploads to PCM wav before upload (see the
frontend `convertToWav`), so this layer no longer shells out to ffmpeg. We read
with libsndfile (bundled in the `soundfile` wheel — no system binary), downmix
to mono, and resample to 24 kHz so the engine receives one shape. libsndfile
also decodes wav/flac/ogg/mp3 directly, which covers the fallback path where the
WebView couldn't decode an exotic upload and sent the original bytes.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from ..domain.errors import AudioConversionError

_TARGET_SAMPLE_RATE = 24_000


def normalize_to_wav(source: Path, destination: Path) -> Path:
    """Convert `source` audio into a mono 24 kHz 16-bit PCM wav at `destination`."""
    try:
        audio, sample_rate = sf.read(str(source), dtype="float32", always_2d=True)
    except Exception as exc:  # libsndfile raises a variety of error types
        raise AudioConversionError(
            f"Could not decode the audio: {exc}"
        ) from exc

    # Downmix to mono — shape is (frames, channels) thanks to always_2d.
    mono = audio.mean(axis=1)

    if sample_rate != _TARGET_SAMPLE_RATE:
        mono = _resample(mono, sample_rate, _TARGET_SAMPLE_RATE)

    destination.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(destination), mono, _TARGET_SAMPLE_RATE, subtype="PCM_16")
    return destination


def _resample(samples: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """High-quality sinc resample via torchaudio (an existing dependency)."""
    import torch
    import torchaudio

    tensor = torch.from_numpy(np.ascontiguousarray(samples)).unsqueeze(0)
    resampled = torchaudio.functional.resample(tensor, orig_sr, target_sr)
    return resampled.squeeze(0).numpy()
