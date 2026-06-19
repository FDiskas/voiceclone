"""HTTP endpoints for synthesizing text in a profile's cloned voice."""

from __future__ import annotations

import struct
from typing import Iterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response, StreamingResponse

from ..cancellation import OperationCancelled
from ..services.synthesis_service import SynthesisService
from .cancellation import run_cancelling_on_disconnect
from .dependencies import get_synthesis_service
from .schemas import SynthesisRequestBody

router = APIRouter(prefix="/api/profiles", tags=["synthesis"])

_FRAME_HEADER = struct.Struct(">I")  # 4-byte big-endian length prefix per chunk

# Nginx's "client closed request" code: the response body is moot (the client
# is gone) but it records that we stopped on purpose rather than failed.
_CLIENT_CLOSED_REQUEST = 499


@router.post("/{profile_id}/speech")
async def synthesize_speech(
    profile_id: str,
    body: SynthesisRequestBody,
    request: Request,
    synthesis: SynthesisService = Depends(get_synthesis_service),
) -> Response:
    try:
        wav_bytes = await run_cancelling_on_disconnect(
            request,
            lambda cancel: synthesis.synthesize(profile_id, body.text, body.speed, cancel),
        )
    except OperationCancelled:
        return Response(status_code=_CLIENT_CLOSED_REQUEST)
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
    stream = synthesis.synthesize_stream(profile_id, body.text, body.speed)

    def frames() -> Iterator[bytes]:
        for chunk in stream.chunks:
            yield _FRAME_HEADER.pack(len(chunk))
            yield chunk

    # Announce the chunk (sentence) count up front so the client can show a
    # progress bar; it's exposed via CORS so the Tauri webview can read it.
    return StreamingResponse(
        frames(),
        media_type="application/octet-stream",
        headers={"X-Total-Chunks": str(stream.total)},
    )
