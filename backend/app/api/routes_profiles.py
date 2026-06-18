"""HTTP endpoints for creating and managing voice profiles."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from ..services.profile_service import ProfileService
from .dependencies import get_profile_service
from .schemas import ProfileResponse

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.get("", response_model=list[ProfileResponse])
def list_profiles(profiles: ProfileService = Depends(get_profile_service)) -> list[ProfileResponse]:
    return [ProfileResponse.from_entity(p) for p in profiles.list_profiles()]


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    name: str = Form(...),
    language: str = Form(...),
    audio: UploadFile = File(...),
    transcript: str | None = Form(default=None),
    profiles: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    audio_bytes = await audio.read()
    profile = profiles.create(
        name=name,
        language=language,
        transcript=transcript,
        audio_bytes=audio_bytes,
        original_filename=audio.filename or "recording.webm",
    )
    return ProfileResponse.from_entity(profile)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    profile_id: str, profiles: ProfileService = Depends(get_profile_service)
) -> None:
    profiles.delete(profile_id)
