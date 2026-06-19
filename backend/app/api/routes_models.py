"""HTTP endpoints to inspect and delete downloaded models.

Lists every managed model (voice engine, transcriber) with its on-disk path
and size, and deletes one by key to reclaim space. Deleting re-downloads on the
next use. Engines/transcribers without a downloadable model simply aren't listed.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ..models import ModelRegistry, UnknownModelError
from .dependencies import get_model_registry
from .schemas import DeletedModelResponse, ModelInfoResponse

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=list[ModelInfoResponse])
def list_models(
    registry: ModelRegistry = Depends(get_model_registry),
) -> list[ModelInfoResponse]:
    return [ModelInfoResponse.from_info(info) for info in registry.list()]


@router.delete("/{key}", response_model=DeletedModelResponse)
def delete_model(
    key: str,
    registry: ModelRegistry = Depends(get_model_registry),
) -> DeletedModelResponse:
    try:
        result = registry.delete(key)
    except UnknownModelError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No managed model with key '{key}'.",
        ) from exc
    return DeletedModelResponse(
        key=result.key,
        repo_id=result.repo_id,
        found=result.found,
        freed_bytes=result.freed_bytes,
    )
