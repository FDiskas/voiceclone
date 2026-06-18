"""The VoiceEngine abstraction (Dependency Inversion boundary).

Services depend on this protocol, never on a concrete TTS library. The real
OmniVoice integration and the in-memory fake both satisfy it, so the rest of
the app — and its tests — are unaware of which one is wired in.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class SynthesisRequest:
    """Everything the engine needs to clone a voice and speak new text."""

    text: str
    reference_audio_path: Path
    reference_text: str
    speed: float = 1.0


@dataclass(frozen=True)
class SynthesisResult:
    """Raw mono PCM audio produced by the engine."""

    samples: "object"  # numpy.ndarray, kept loose to avoid a hard numpy import here
    sample_rate: int


class VoiceEngine(Protocol):
    """Clones a reference voice and synthesizes arbitrary text in it."""

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        ...
