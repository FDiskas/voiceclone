"""HTTP endpoints reporting (and triggering) voice-engine readiness.

The desktop app polls `/api/engine/status` to show a download/load indicator,
and POSTs `/api/engine/warmup` when the user opts to download the model. Model
deletion / disk inspection lives under `/api/models` (see `routes_models`).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..engine.base import VoiceEngine
from ..engine.readiness import status_of, warm_up
from .dependencies import get_voice_engine
from .schemas import EngineStatusResponse

router = APIRouter(prefix="/api/engine", tags=["engine"])


@router.get("/status", response_model=EngineStatusResponse)
def engine_status(engine: VoiceEngine = Depends(get_voice_engine)) -> EngineStatusResponse:
    return EngineStatusResponse.from_status(status_of(engine))


@router.post("/warmup", response_model=EngineStatusResponse)
def engine_warmup(engine: VoiceEngine = Depends(get_voice_engine)) -> EngineStatusResponse:
    """Begin loading the model now (idempotent); returns the current status."""
    warm_up(engine)
    return EngineStatusResponse.from_status(status_of(engine))
