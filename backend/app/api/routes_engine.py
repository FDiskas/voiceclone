"""HTTP endpoints reporting (and triggering) voice-engine readiness.

The desktop app polls `/api/engine/status` on launch to show a download/load
indicator, because the real model is fetched from Hugging Face on first run.
It can also delete the downloaded model to reclaim disk / force a re-download.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ..engine.base import VoiceEngine
from ..engine.management import (
    ModelManagementUnsupported,
    delete_model,
    is_manageable,
)
from ..engine.readiness import status_of, warm_up
from .dependencies import get_voice_engine
from .schemas import DeletedModelResponse, EngineStatusResponse

router = APIRouter(prefix="/api/engine", tags=["engine"])


@router.get("/status", response_model=EngineStatusResponse)
def engine_status(engine: VoiceEngine = Depends(get_voice_engine)) -> EngineStatusResponse:
    return EngineStatusResponse.from_status(status_of(engine), manageable=is_manageable(engine))


@router.post("/warmup", response_model=EngineStatusResponse)
def engine_warmup(engine: VoiceEngine = Depends(get_voice_engine)) -> EngineStatusResponse:
    """Begin loading the model now (idempotent); returns the current status."""
    warm_up(engine)
    return EngineStatusResponse.from_status(status_of(engine), manageable=is_manageable(engine))


@router.delete("/model", response_model=DeletedModelResponse)
def engine_delete_model(
    engine: VoiceEngine = Depends(get_voice_engine),
) -> DeletedModelResponse:
    """Delete the downloaded model so it re-downloads on the next warm-up."""
    try:
        result = delete_model(engine)
    except ModelManagementUnsupported as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return DeletedModelResponse(
        repo_id=result.repo_id,
        found=result.found,
        freed_bytes=result.freed_bytes,
    )
