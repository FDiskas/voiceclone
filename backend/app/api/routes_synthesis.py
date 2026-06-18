"""HTTP endpoints for synthesizing text in a profile's cloned voice."""

from __future__ import annotations

import struct
from typing import Iterator

from fastapi import APIRouter, Depends
from fastapi.responses import Response, StreamingResponse

from ..services.synthesis_service import SynthesisService
from .dependencies import get_synthesis_service
from .schemas import SynthesisRequestBody

router = APIRouter(prefix="/api/profiles", tags=["synthesis"])

_FRAME_HEADER = struct.Struct(">I")  # 4-byte big-endian length prefix per chunk


@router.post("/{profile_id}/speech")
def synthesize_speech(
    profile_id: str,
    body: SynthesisRequestBody,
    synthesis: SynthesisService = Depends(get_synthesis_service),
) -> Response:
    wav_bytes = synthesis.synthesize(profile_id, body.text, body.speed)
    return Response(content=wav_bytes, media_type="audio/wav")


@router.post("/{profile_id}/speech/stream")
def synthesize_speech_stream(
    profile_id: str,
    body: SynthesisRequestBody,
    synthesis: SynthesisService = Depends(get_synthesis_service),
) -> StreamingResponse:
    """Stream one length-prefixed wav per sentence as each finishes rendering.

    Wire format: repeated [uint32 big-endian length][wav bytes]. The client
    decodes and plays each chunk back-to-back for progressive playback.
    """

    # Called eagerly: validation + profile lookup run now, so errors map to a
    # normal HTTP response instead of surfacing after streaming has begun.
    chunks = synthesis.synthesize_stream(profile_id, body.text, body.speed)

    def frames() -> Iterator[bytes]:
        for chunk in chunks:
            yield _FRAME_HEADER.pack(len(chunk))
            yield chunk

    return StreamingResponse(frames(), media_type="application/octet-stream")
