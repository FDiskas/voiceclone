"""Application settings, loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_data_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VOICECLONE_", env_file=".env", extra="ignore")

    # Which engine to wire in: "fake" (no model) or "omnivoice" (real).
    engine: str = "fake"

    # OmniVoice configuration (only used when engine == "omnivoice").
    model_id: str = "k2-fsa/OmniVoice"
    device: str = "auto"  # auto -> cuda / mps / cpu
    dtype: str = "auto"  # auto -> float16 on gpu, float32 on cpu
    num_step: int = 32

    # Transcription: "fake" (placeholder) or "whisper" (faster-whisper).
    transcriber: str = "fake"
    whisper_model_size: str = "base"
    whisper_compute_type: str = "auto"  # auto -> int8 on cpu, float16 on gpu

    # Storage.
    data_dir: Path = Field(default_factory=_default_data_dir)

    # CORS origins for the Vite dev server.
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @property
    def db_path(self) -> Path:
        return self.data_dir / "voiceclone.db"

    @property
    def audio_dir(self) -> Path:
        return self.data_dir / "audio"

    def resolved_device(self) -> str:
        if self.device != "auto":
            return self.device
        try:
            import torch

            if torch.cuda.is_available():
                return "cuda:0"
            if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        return "cpu"

    def resolved_dtype(self, device: str) -> str:
        if self.dtype != "auto":
            return self.dtype
        return "float16" if device.startswith("cuda") else "float32"

    def resolved_whisper_device(self) -> str:
        # faster-whisper supports only "cpu"/"cuda"; map mps -> cpu.
        device = self.resolved_device()
        return "cuda" if device.startswith("cuda") else "cpu"

    def resolved_whisper_compute_type(self, device: str) -> str:
        if self.whisper_compute_type != "auto":
            return self.whisper_compute_type
        return "float16" if device.startswith("cuda") else "int8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
