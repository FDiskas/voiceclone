"""A deterministic fake engine for development and tests.

Generates a short sine tone instead of real speech, so the full app can run
end-to-end without downloading the OmniVoice model or owning a GPU.
"""

from __future__ import annotations

import math

from .base import SynthesisRequest, SynthesisResult

_SAMPLE_RATE = 24_000


class FakeVoiceEngine:
    """Returns a tone whose length scales with the requested text length."""

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        import numpy as np

        seconds = max(0.5, min(5.0, len(request.text) / 20))
        frames = int(_SAMPLE_RATE * seconds / request.speed)
        t = np.linspace(0, seconds, frames, endpoint=False)
        samples = (0.2 * np.sin(2 * math.pi * 220 * t)).astype(np.float32)
        return SynthesisResult(samples=samples, sample_rate=_SAMPLE_RATE)
