"""FastAPI application factory and error mapping."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .domain.errors import (
    AudioConversionError,
    DomainError,
    ProfileNotFoundError,
    SynthesisError,
    ValidationError,
)
from .api import (
    routes_engine,
    routes_models,
    routes_profiles,
    routes_synthesis,
    routes_transcription,
)

_ERROR_STATUS: dict[type[DomainError], int] = {
    ValidationError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    ProfileNotFoundError: status.HTTP_404_NOT_FOUND,
    AudioConversionError: status.HTTP_400_BAD_REQUEST,
    SynthesisError: status.HTTP_502_BAD_GATEWAY,
}


def create_app() -> FastAPI:
    settings = get_settings()
    # The model is loaded on demand (the user clicks "Download" in the UI, which
    # hits POST /api/engine/warmup) rather than eagerly at startup — a cold first
    # launch shouldn't pull hundreds of MB before the user has asked for it.
    app = FastAPI(title="VoiceClone API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        # Custom response headers JS must be able to read cross-origin (the
        # Tauri webview is a different origin than the sidecar backend).
        expose_headers=["X-Total-Chunks"],
    )

    app.include_router(routes_profiles.router)
    app.include_router(routes_synthesis.router)
    app.include_router(routes_transcription.router)
    app.include_router(routes_engine.router)
    app.include_router(routes_models.router)

    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        code = _ERROR_STATUS.get(type(exc), status.HTTP_400_BAD_REQUEST)
        return JSONResponse(status_code=code, content={"detail": str(exc)})

    @app.get("/api/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok", "engine": settings.engine}

    return app


app = create_app()
