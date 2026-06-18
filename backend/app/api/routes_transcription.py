"""HTTP endpoint for auto-transcribing a reference clip (Whisper)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from ..services.transcription_service import TranscriptionService
from .dependencies import get_transcription_service
from .schemas import TranscriptionResponse

router = APIRouter(prefix="/api", tags=["transcription"])


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(
    audio: UploadFile = File(...),
    language: str | None = Form(default=None),
    transcription: TranscriptionService = Depends(get_transcription_service),
) -> TranscriptionResponse:
    audio_bytes = await audio.read()
    text = transcription.transcribe(
        audio_bytes,
        original_filename=audio.filename or "recording.webm",
        language=language,
    )
    return TranscriptionResponse(text=text)
