"""HTTP endpoints for creating and managing voice profiles."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

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


@router.get("/{profile_id}/audio")
def get_profile_audio(
    profile_id: str, profiles: ProfileService = Depends(get_profile_service)
) -> FileResponse:
    """Serve the profile's normalized reference audio (24 kHz mono wav)."""
    profile = profiles.get(profile_id)  # raises ProfileNotFoundError -> 404
    path = profile.reference_audio_path
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reference audio not found"
        )
    return FileResponse(
        path, media_type="audio/wav", filename=f"{profile.name.value}.wav"
    )


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    profile_id: str, profiles: ProfileService = Depends(get_profile_service)
) -> None:
    profiles.delete(profile_id)
