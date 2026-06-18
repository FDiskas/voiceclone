import io

import pytest
import soundfile as sf

from app.domain.errors import ProfileNotFoundError, ValidationError


def _create_profile(profile_service):
    return profile_service.create(
        name="My Voice",
        language="en",
        transcript="This is a reference recording.",
        audio_bytes=b"fake-audio-bytes",
        original_filename="recording.webm",
    )


def test_synthesis_returns_playable_wav(profile_service, synthesis_service):
    profile = _create_profile(profile_service)

    wav_bytes = synthesis_service.synthesize(profile.id.value, "Hello world")

    samples, sample_rate = sf.read(io.BytesIO(wav_bytes))
    assert sample_rate == 24_000
    assert len(samples) > 0


def test_longer_text_yields_longer_audio(profile_service, synthesis_service):
    profile = _create_profile(profile_service)

    short = synthesis_service.synthesize(profile.id.value, "Hi")
    long = synthesis_service.synthesize(profile.id.value, "word " * 60)

    assert len(long) > len(short)


def test_empty_text_is_rejected(profile_service, synthesis_service):
    profile = _create_profile(profile_service)
    with pytest.raises(ValidationError):
        synthesis_service.synthesize(profile.id.value, "   ")


def test_synthesis_for_unknown_profile_raises(synthesis_service):
    with pytest.raises(ProfileNotFoundError):
        synthesis_service.synthesize("nope", "Hello")


# Two sentences long enough that they exceed the merge budget and stay separate.
_TWO_SENTENCES = ("word " * 40).strip() + ". " + ("alpha " * 40).strip() + "."


def test_streaming_yields_one_wav_per_sentence(profile_service, synthesis_service):
    profile = _create_profile(profile_service)

    chunks = list(synthesis_service.synthesize_stream(profile.id.value, _TWO_SENTENCES))

    assert len(chunks) == 2
    for chunk in chunks:
        samples, sample_rate = sf.read(io.BytesIO(chunk))
        assert sample_rate == 24_000
        assert len(samples) > 0


def test_streaming_validates_eagerly_for_unknown_profile(synthesis_service):
    # Must raise on the call, not lazily once the stream is consumed.
    with pytest.raises(ProfileNotFoundError):
        synthesis_service.synthesize_stream("nope", "Hello there.")
