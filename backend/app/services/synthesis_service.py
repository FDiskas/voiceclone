"""Use case: speak new text in a stored profile's voice."""

from __future__ import annotations

from typing import Iterator

from ..audio.wav import encode_wav
from ..domain.profile import VoiceProfile
from ..domain.values import SpeechText
from ..engine.base import SynthesisRequest, VoiceEngine
from ..text.segmentation import split_into_sentences
from .profile_service import ProfileService


class SynthesisService:
    """Coordinates a profile lookup and a voice-engine synthesis."""

    def __init__(self, profiles: ProfileService, engine: VoiceEngine) -> None:
        self._profiles = profiles
        self._engine = engine

    def synthesize(self, profile_id: str, text: str, speed: float = 1.0) -> bytes:
        """Render the whole text into a single wav."""
        speech = SpeechText(text)
        profile = self._profiles.get(profile_id)
        result = self._engine.synthesize(self._request_for(profile, speech.value, speed))
        return encode_wav(result.samples, result.sample_rate)

    def synthesize_stream(
        self, profile_id: str, text: str, speed: float = 1.0
    ) -> Iterator[bytes]:
        """Render sentence by sentence, yielding each chunk's wav as it is ready.

        The profile lookup and text validation happen eagerly (before any
        audio is yielded) so errors surface as a normal response rather than
        mid-stream, after a 200 has already been sent.
        """
        speech = SpeechText(text)
        profile = self._profiles.get(profile_id)
        sentences = split_into_sentences(speech.value)

        def chunks() -> Iterator[bytes]:
            for sentence in sentences:
                result = self._engine.synthesize(self._request_for(profile, sentence, speed))
                yield encode_wav(result.samples, result.sample_rate)

        return chunks()

    @staticmethod
    def _request_for(profile: VoiceProfile, text: str, speed: float) -> SynthesisRequest:
        return SynthesisRequest(
            text=text,
            reference_audio_path=profile.reference_audio_path,
            reference_text=profile.transcript.value,
            speed=speed,
        )
