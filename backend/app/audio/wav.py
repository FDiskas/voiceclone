"""Encode raw PCM samples into a self-contained wav byte string."""

from __future__ import annotations

import io


def encode_wav(samples, sample_rate: int) -> bytes:
    """Serialize mono float samples as a 16-bit PCM wav."""
    import soundfile as sf

    buffer = io.BytesIO()
    sf.write(buffer, samples, sample_rate, format="WAV", subtype="PCM_16")
    return buffer.getvalue()
