"""HTTP endpoint for auto-transcribing a reference clip (Whisper)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import Response

from ..cancellation import OperationCancelled
from ..services.transcription_service import TranscriptionService
from .cancellation import run_cancelling_on_disconnect
from .dependencies import get_transcription_service
from .schemas import TranscriptionResponse

router = APIRouter(prefix="/api", tags=["transcription"])

_CLIENT_CLOSED_REQUEST = 499  # client aborted; stopped on purpose, not a failure


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(
    request: Request,
    audio: UploadFile = File(...),
    language: str | None = Form(default=None),
    transcription: TranscriptionService = Depends(get_transcription_service),
) -> Response:
    audio_bytes = await audio.read()
    filename = audio.filename or "recording.webm"
    try:
        text = await run_cancelling_on_disconnect(
            request,
            lambda cancel: transcription.transcribe(
                audio_bytes, original_filename=filename, language=language, cancel=cancel
            ),
        )
    except OperationCancelled:
        return Response(status_code=_CLIENT_CLOSED_REQUEST)
    return TranscriptionResponse(text=text)
