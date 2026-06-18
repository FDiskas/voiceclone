"""Pydantic DTOs for request bodies and responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from ..domain.profile import VoiceProfile
from ..engine.readiness import EngineStatus


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


class EngineStatusResponse(BaseModel):
    """Readiness of the voice engine, polled by the UI on first launch."""

    state: str  # idle | downloading | loading | ready | error
    message: str
    progress: float | None = None  # 0..1 when known, else null (indeterminate)
    detail: str | None = None  # error text when state == "error"
    manageable: bool = False  # whether the model can be deleted/re-downloaded

    @classmethod
    def from_status(cls, status: EngineStatus, manageable: bool = False) -> "EngineStatusResponse":
        return cls(
            state=status.state,
            message=status.message,
            progress=status.progress,
            detail=status.detail,
            manageable=manageable,
        )


class DeletedModelResponse(BaseModel):
    """Result of deleting the downloaded model from the local cache."""

    repo_id: str
    found: bool
    freed_bytes: int
