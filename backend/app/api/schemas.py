"""Pydantic DTOs for request bodies and responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from ..domain.profile import VoiceProfile
from ..engine.readiness import EngineStatus
from ..models.managed_model import DeletedModel, ModelInfo


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

    @classmethod
    def from_status(cls, status: EngineStatus) -> "EngineStatusResponse":
        return cls(
            state=status.state,
            message=status.message,
            progress=status.progress,
            detail=status.detail,
        )


class ModelInfoResponse(BaseModel):
    """A managed model's identity and on-disk footprint, for the settings UI."""

    key: str
    label: str
    repo_id: str
    downloaded: bool
    path: str | None = None
    size_bytes: int = 0

    @classmethod
    def from_info(cls, info: ModelInfo) -> "ModelInfoResponse":
        return cls(
            key=info.key,
            label=info.label,
            repo_id=info.repo_id,
            downloaded=info.downloaded,
            path=info.path,
            size_bytes=info.size_bytes,
        )


class DeletedModelResponse(BaseModel):
    """Result of deleting a downloaded model from the local cache."""

    key: str
    repo_id: str
    found: bool
    freed_bytes: int
