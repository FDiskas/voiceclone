"""Use case: speak new text in a stored profile's voice."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from ..audio.wav import encode_wav
from ..cancellation import CancellationToken, raise_if_cancelled
from ..domain.profile import VoiceProfile
from ..domain.values import SpeechText
from ..engine.base import SynthesisRequest, SynthesisResult, VoiceEngine
from ..text.segmentation import split_into_sentences
from .profile_service import ProfileService


@dataclass(frozen=True)
class StreamedSynthesis:
    """A sentence-by-sentence synthesis whose size is known before it runs.

    Segmentation happens eagerly, so `total` (the number of wav chunks that
    will be yielded) is available up front — the API announces it so the client
    can show real progress — while `chunks` renders lazily, one wav per
    sentence as each finishes.
    """

    total: int
    chunks: Iterator[bytes]


class SynthesisService:
    """Coordinates a profile lookup and a voice-engine synthesis."""

    def __init__(self, profiles: ProfileService, engine: VoiceEngine) -> None:
        self._profiles = profiles
        self._engine = engine

    def synthesize(
        self,
        profile_id: str,
        text: str,
        speed: float = 1.0,
        cancel: CancellationToken | None = None,
    ) -> bytes:
        """Render the whole text into a single wav.

        Rendered sentence by sentence (the same unit streaming uses) and joined,
        so a cancelled request can stop between sentences and free the engine
        promptly instead of running the whole text first.
        """
        import numpy as np

        profile, sentences = self._prepare(profile_id, text)
        results = list(self._render(profile, sentences, speed, cancel))
        samples = np.concatenate([result.samples for result in results])
        return encode_wav(samples, results[0].sample_rate)

    def synthesize_stream(
        self, profile_id: str, text: str, speed: float = 1.0
    ) -> StreamedSynthesis:
        """Render sentence by sentence, yielding each chunk's wav as it is ready.

        The profile lookup, text validation, and segmentation happen eagerly
        (before any audio is yielded) so errors surface as a normal response
        rather than mid-stream after a 200 has been sent, and so the chunk
        count is known up front for progress reporting.

        Cancellation is handled by the transport: the server stops pulling from
        this generator when the client disconnects, so the engine pauses at the
        next sentence boundary on its own — no token needed here.
        """
        profile, sentences = self._prepare(profile_id, text)

        def chunks() -> Iterator[bytes]:
            for result in self._render(profile, sentences, speed):
                yield encode_wav(result.samples, result.sample_rate)

        return StreamedSynthesis(total=len(sentences), chunks=chunks())

    def _prepare(self, profile_id: str, text: str) -> tuple[VoiceProfile, list[str]]:
        """Validate text, resolve the profile, and segment — all eagerly."""
        speech = SpeechText(text)
        profile = self._profiles.get(profile_id)
        return profile, split_into_sentences(speech.value)

    def _render(
        self,
        profile: VoiceProfile,
        sentences: list[str],
        speed: float,
        cancel: CancellationToken | None = None,
    ) -> Iterator[SynthesisResult]:
        """Synthesize each sentence, checking for cancellation between them."""
        for sentence in sentences:
            raise_if_cancelled(cancel)
            yield self._engine.synthesize(self._request_for(profile, sentence, speed))

    @staticmethod
    def _request_for(profile: VoiceProfile, text: str, speed: float) -> SynthesisRequest:
        return SynthesisRequest(
            text=text,
            reference_audio_path=profile.reference_audio_path,
            reference_text=profile.transcript.value,
            speed=speed,
        )
