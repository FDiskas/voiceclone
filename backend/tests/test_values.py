import pytest

from app.domain.errors import ValidationError
from app.domain.values import Language, SpeechText, Transcript, VoiceName


def test_voice_name_strips_surrounding_whitespace():
    assert VoiceName("  My Voice  ").value == "My Voice"


def test_empty_voice_name_is_rejected():
    with pytest.raises(ValidationError):
        VoiceName("   ")


@pytest.mark.parametrize("code", ["en", "lt", "pt-BR", "zh-Hans"])
def test_valid_language_tags_are_accepted(code):
    assert Language(code).code == code


@pytest.mark.parametrize("code", ["", "english", "123", "e"])
def test_invalid_language_tags_are_rejected(code):
    with pytest.raises(ValidationError):
        Language(code)


def test_empty_transcript_is_rejected():
    with pytest.raises(ValidationError):
        Transcript("")


def test_empty_speech_text_is_rejected():
    with pytest.raises(ValidationError):
        SpeechText("  ")
