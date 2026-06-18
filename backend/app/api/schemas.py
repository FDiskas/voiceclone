"""Pydantic DTOs for request bodies and responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from ..domain.profile import VoiceProfile


class ProfileResponse(BaseModel):
    id: str
    name: str
    language: str
    transcript: str
    created_at: datetime

    @classmethod
    def from_entity(cls, profile: VoiceProfile) -> "ProfileResponse":
        return cls(
            id=profile.id.value,
            name=profile.name.value,
            language=profile.language.code,
            transcript=profile.transcript.value,
            created_at=profile.created_at,
        )


class SynthesisRequestBody(BaseModel):
    text: str = Field(..., min_length=1)
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


class TranscriptionResponse(BaseModel):
    text: str
