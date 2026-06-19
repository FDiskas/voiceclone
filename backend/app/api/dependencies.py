"""Composition root: wires concrete implementations together once.

FastAPI route handlers depend on these provider functions, never on
constructors directly, so swapping the engine or storage is a one-line change.
"""

from __future__ import annotations

from functools import lru_cache

from ..config import Settings, get_settings
from ..engine.base import VoiceEngine
from ..engine.fake_engine import FakeVoiceEngine
from ..engine.omnivoice_engine import OmniVoiceEngine
from ..models import ModelRegistry, is_managed
from ..services.profile_service import ProfileService
from ..services.synthesis_service import SynthesisService
from ..services.transcription_service import TranscriptionService
from ..storage.database import Database
from ..storage.profile_repository import ProfileRepository
from ..transcription.base import Transcriber
from ..transcription.fake_transcriber import FakeTranscriber
from ..transcription.whisper_transcriber import WhisperTranscriber


@lru_cache
def get_database() -> Database:
    return Database(get_settings().db_path)


@lru_cache
def get_transcriber() -> Transcriber:
    settings = get_settings()
    if settings.transcriber == "fake":
        return FakeTranscriber()
    if settings.transcriber == "whisper":
        device = settings.resolved_whisper_device()
        return WhisperTranscriber(
            model_size=settings.whisper_model_size,
            device=device,
            compute_type=settings.resolved_whisper_compute_type(device),
        )
    raise ValueError(f"unknown transcriber '{settings.transcriber}' (expected 'fake' or 'whisper')")


@lru_cache
def get_transcription_service() -> TranscriptionService:
    return TranscriptionService(get_transcriber())


@lru_cache
def get_profile_service() -> ProfileService:
    settings = get_settings()
    repository = ProfileRepository(get_database())
    return ProfileService(repository, settings.audio_dir, get_transcriber())


@lru_cache
def get_voice_engine() -> VoiceEngine:
    settings = get_settings()
    if settings.engine == "fake":
        return FakeVoiceEngine()
    if settings.engine == "omnivoice":
        return _build_omnivoice(settings)
    raise ValueError(f"unknown engine '{settings.engine}' (expected 'fake' or 'omnivoice')")


def _build_omnivoice(settings: Settings) -> OmniVoiceEngine:
    device = settings.resolved_device()
    return OmniVoiceEngine(
        model_id=settings.model_id,
        device_map=device,
        dtype=settings.resolved_dtype(device),
        num_step=settings.num_step,
        mps_high_watermark_ratio=settings.mps_high_watermark_ratio,
    )


@lru_cache
def get_synthesis_service() -> SynthesisService:
    return SynthesisService(get_profile_service(), get_voice_engine())


@lru_cache
def get_model_registry() -> ModelRegistry:
    """Every active component that owns a downloadable model (engine, transcriber)."""
    candidates = (get_voice_engine(), get_transcriber())
    return ModelRegistry(c for c in candidates if is_managed(c))
