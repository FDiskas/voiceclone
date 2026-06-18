"""The VoiceProfile entity: a stored reference voice the user can reuse."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .values import Language, ProfileId, Transcript, VoiceName


@dataclass(frozen=True)
class VoiceProfile:
    """An anonymous, reusable cloned-voice reference.

    Because OmniVoice is zero-shot there is no trained model per profile:
    a profile is simply the reference audio plus the metadata needed to
    re-clone the voice on every synthesis call.
    """

    id: ProfileId
    name: VoiceName
    language: Language
    transcript: Transcript
    reference_audio_path: Path
    created_at: datetime
