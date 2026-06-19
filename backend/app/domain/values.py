"""Value objects for the voice-cloning domain.

Primitives (ids, names, transcripts, language codes) are wrapped so that
validation lives in one place and invalid values cannot be constructed.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from .errors import ValidationError

_MAX_NAME_LENGTH = 80
_MAX_TRANSCRIPT_LENGTH = 2_000
_MAX_SYNTHESIS_LENGTH = 50_000
_LANGUAGE_PATTERN = re.compile(r"^[a-z]{2,3}(-[A-Za-z0-9]{2,8})?$")


@dataclass(frozen=True)
class ProfileId:
    """The stable, opaque identifier of a voice profile."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValidationError("profile id must not be empty")

    @staticmethod
    def generate() -> "ProfileId":
        return ProfileId(uuid.uuid4().hex)


@dataclass(frozen=True)
class VoiceName:
    """A human-friendly label the user gives a profile."""

    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip()
        if not cleaned:
            raise ValidationError("profile name must not be empty")
        if len(cleaned) > _MAX_NAME_LENGTH:
            raise ValidationError(f"profile name must be at most {_MAX_NAME_LENGTH} characters")
        object.__setattr__(self, "value", cleaned)


@dataclass(frozen=True)
class Language:
    """A BCP-47-ish language tag, kept as profile metadata.

    OmniVoice infers language from the text itself, so this is used for
    display and to give context to the reference transcript.
    """

    code: str

    def __post_init__(self) -> None:
        cleaned = self.code.strip()
        if not _LANGUAGE_PATTERN.match(cleaned):
            raise ValidationError(f"'{self.code}' is not a valid language tag (e.g. 'en', 'lt', 'pt-BR')")
        object.__setattr__(self, "code", cleaned)


@dataclass(frozen=True)
class Transcript:
    """The transcription of a reference recording."""

    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip()
        if not cleaned:
            raise ValidationError("transcript must not be empty")
        if len(cleaned) > _MAX_TRANSCRIPT_LENGTH:
            raise ValidationError(f"transcript must be at most {_MAX_TRANSCRIPT_LENGTH} characters")
        object.__setattr__(self, "value", cleaned)


@dataclass(frozen=True)
class SpeechText:
    """The new text a user wants spoken in a cloned voice."""

    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip()
        if not cleaned:
            raise ValidationError("text to synthesize must not be empty")
        if len(cleaned) > _MAX_SYNTHESIS_LENGTH:
            raise ValidationError(f"text must be at most {_MAX_SYNTHESIS_LENGTH} characters")
        object.__setattr__(self, "value", cleaned)
