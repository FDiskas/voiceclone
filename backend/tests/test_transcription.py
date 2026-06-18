from app.transcription.fake_transcriber import FakeTranscriber


def _create_without_transcript(profile_service):
    return profile_service.create(
        name="My Voice",
        language="en",
        audio_bytes=b"fake-audio-bytes",
        original_filename="recording.webm",
    )


def test_missing_transcript_is_auto_filled(profile_service):
    profile = _create_without_transcript(profile_service)
    assert profile.transcript.value == FakeTranscriber().transcribe(profile.reference_audio_path)


def test_provided_transcript_is_kept_verbatim(profile_service):
    profile = profile_service.create(
        name="My Voice",
        language="en",
        audio_bytes=b"data",
        original_filename="a.wav",
        transcript="My own words.",
    )
    assert profile.transcript.value == "My own words."


def test_transcription_service_normalizes_then_transcribes(transcription_service):
    text = transcription_service.transcribe(b"audio", "clip.webm", language="en")
    assert text == FakeTranscriber().transcribe(None)
