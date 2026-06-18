import pytest

from app.domain.errors import ProfileNotFoundError, ValidationError


def _create_sample(profile_service, name="My Voice"):
    return profile_service.create(
        name=name,
        language="en",
        transcript="This is a reference recording.",
        audio_bytes=b"fake-audio-bytes",
        original_filename="recording.webm",
    )


def test_created_profile_is_persisted_and_audio_written(profile_service):
    profile = _create_sample(profile_service)

    assert profile.name.value == "My Voice"
    assert profile.reference_audio_path.exists()
    assert profile_service.get(profile.id.value).id == profile.id


def test_listing_returns_created_profiles(profile_service):
    _create_sample(profile_service, name="One")
    _create_sample(profile_service, name="Two")

    names = {p.name.value for p in profile_service.list_profiles()}
    assert names == {"One", "Two"}


def test_invalid_language_is_rejected_before_writing_audio(profile_service):
    with pytest.raises(ValidationError):
        profile_service.create(
            name="x",
            language="not-a-language!!",
            transcript="hello",
            audio_bytes=b"data",
            original_filename="a.wav",
        )


def test_deleting_profile_removes_row_and_file(profile_service):
    profile = _create_sample(profile_service)
    path = profile.reference_audio_path

    profile_service.delete(profile.id.value)

    assert not path.exists()
    with pytest.raises(ProfileNotFoundError):
        profile_service.get(profile.id.value)


def test_getting_unknown_profile_raises(profile_service):
    with pytest.raises(ProfileNotFoundError):
        profile_service.get("does-not-exist")
