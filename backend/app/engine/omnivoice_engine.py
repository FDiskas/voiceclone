"""The real OmniVoice adapter — the only module that imports `omnivoice`.

OmniVoice (https://github.com/k2-fsa/OmniVoice) is a zero-shot multilingual
TTS model. The weights are loaded lazily and can be *warmed up* in the
background so the UI can show download/load progress before the first
synthesis (the weights download from Hugging Face on first run, which can take
minutes). See `readiness.py` for the capability contract this satisfies.
"""

from __future__ import annotations

import logging
import threading

from ..domain.errors import SynthesisError
from .base import SynthesisRequest, SynthesisResult
from .hf_progress import capture_download_progress
from .management import DeletedModel
from .readiness import (
    STATE_DOWNLOADING,
    STATE_ERROR,
    STATE_IDLE,
    STATE_LOADING,
    STATE_READY,
    EngineStatus,
)

_OUTPUT_SAMPLE_RATE = 24_000
_logger = logging.getLogger(__name__)


class OmniVoiceEngine:
    """Wraps `omnivoice.OmniVoice` behind the VoiceEngine + WarmableEngine protocols."""

    def __init__(
        self,
        model_id: str,
        device_map: str,
        dtype: str,
        num_step: int = 32,
        mps_high_watermark_ratio: float = 0.0,
    ) -> None:
        self._model_id = model_id
        self._device_map = device_map
        self._dtype = dtype
        self._num_step = num_step
        self._mps_high_watermark_ratio = mps_high_watermark_ratio
        self._model = None

        # Readiness state, guarded by `_state_lock`. `_load_lock` serialises the
        # actual (slow) load so a synthesis call and a warm-up can't load twice.
        # `_infer_lock` serialises generation so concurrent requests can't stack
        # multiple model passes in (unified/GPU) memory at once.
        self._state_lock = threading.Lock()
        self._load_lock = threading.Lock()
        self._infer_lock = threading.Lock()
        self._warm_thread: threading.Thread | None = None
        self._state = STATE_IDLE
        self._message = "Voice model not loaded yet."
        self._progress: float | None = None
        self._detail: str | None = None

    # --- WarmableEngine -------------------------------------------------

    def warm_up(self) -> None:
        """Load the model in the background (idempotent, non-blocking)."""
        with self._state_lock:
            if self._state in (STATE_DOWNLOADING, STATE_LOADING, STATE_READY):
                return
            if self._warm_thread is not None and self._warm_thread.is_alive():
                return
            self._state = STATE_LOADING
            self._message = "Preparing voice model…"
            self._progress = None
            self._detail = None
            self._warm_thread = threading.Thread(
                target=self._warm, name="omnivoice-warmup", daemon=True
            )
            self._warm_thread.start()

    def status(self) -> EngineStatus:
        with self._state_lock:
            return EngineStatus(
                state=self._state,
                message=self._message,
                progress=self._progress,
                detail=self._detail,
            )

    # --- ManagedModelEngine ---------------------------------------------

    def delete_model(self) -> DeletedModel:
        """Unload the model and purge its cache so it re-downloads next time."""
        # Wait for any in-flight load to finish, then drop the in-memory model.
        with self._load_lock:
            self._model = None
            freed, found = self._purge_cache()
        with self._state_lock:
            self._state = STATE_IDLE
            self._message = "Voice model not loaded yet."
            self._progress = None
            self._detail = None
        _logger.info(
            "Deleted OmniVoice model %s (found=%s, freed=%d bytes)",
            self._model_id,
            found,
            freed,
        )
        return DeletedModel(repo_id=self._model_id, found=found, freed_bytes=freed)

    def _purge_cache(self) -> tuple[int, bool]:
        """Remove this model's revisions from the Hugging Face cache."""
        try:
            from huggingface_hub import scan_cache_dir
        except Exception:  # noqa: BLE001 - hub absent: nothing cached to remove
            return 0, False

        cache = scan_cache_dir()
        commit_hashes: list[str] = []
        freed = 0
        for repo in cache.repos:
            if repo.repo_id == self._model_id:
                freed += repo.size_on_disk
                commit_hashes.extend(rev.commit_hash for rev in repo.revisions)
        if not commit_hashes:
            return 0, False
        cache.delete_revisions(*commit_hashes).execute()
        return freed, True

    def _warm(self) -> None:
        try:
            self._load()
        except Exception as exc:  # noqa: BLE001 - report instead of crashing the thread
            _logger.exception("OmniVoice warm-up failed")
            with self._state_lock:
                self._state = STATE_ERROR
                self._message = "Voice model failed to load."
                self._detail = str(exc)
                self._progress = None

    # --- progress plumbing ----------------------------------------------

    def _on_download_progress(self, downloaded: int, total: int) -> None:
        with self._state_lock:
            self._state = STATE_DOWNLOADING
            self._progress = (downloaded / total) if total else None
            if total:
                self._message = f"Downloading voice model… {downloaded / total:.0%}"
            else:
                self._message = "Downloading voice model…"

    def _mark(self, state: str, message: str, progress: float | None = None) -> None:
        with self._state_lock:
            self._state = state
            self._message = message
            self._progress = progress
            self._detail = None

    # --- loading --------------------------------------------------------

    def _load(self):
        if self._model is not None:
            return self._model
        with self._load_lock:
            if self._model is not None:
                return self._model
            try:
                import torch
                from omnivoice import OmniVoice
            except ImportError as exc:  # pragma: no cover - depends on optional deps
                raise SynthesisError(
                    "omnivoice is not installed. Run `pip install omnivoice` or use ENGINE=fake."
                ) from exc

            self._apply_mps_memory_cap()
            dtype = getattr(torch, self._dtype, torch.float32)
            _logger.info("Loading OmniVoice model %s on %s", self._model_id, self._device_map)
            self._mark(STATE_LOADING, "Preparing voice model…")
            # The download (if any) happens inside from_pretrained; capture its
            # progress, then report the in-memory/device load that follows.
            with capture_download_progress(self._on_download_progress):
                self._model = OmniVoice.from_pretrained(
                    self._model_id, device_map=self._device_map, dtype=dtype
                )
            self._mark(STATE_READY, "Voice model ready.", progress=1.0)
        return self._model

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        model = self._load()
        import torch

        # Serialise generation: two concurrent passes would stack their working
        # set in (unified) memory and can OOM — on Apple Silicon hard enough to
        # take the whole OS down. One synthesis at a time keeps peak bounded.
        with self._infer_lock:
            try:
                # inference_mode is lighter than the default no_grad path: no
                # autograd bookkeeping, so intermediates are freed eagerly.
                with torch.inference_mode():
                    audio = model.generate(
                        text=request.text,
                        ref_audio=str(request.reference_audio_path),
                        ref_text=request.reference_text,
                        num_step=self._num_step,
                        speed=request.speed,
                    )
            except Exception as exc:  # noqa: BLE001 - surface any engine failure uniformly
                raise SynthesisError(f"OmniVoice failed to synthesize: {exc}") from exc
            finally:
                # Return cached blocks to the allocator between sentences so a
                # multi-sentence stream doesn't accumulate device memory.
                self._release_device_memory(torch)

        return SynthesisResult(samples=audio[0], sample_rate=_OUTPUT_SAMPLE_RATE)

    def _apply_mps_memory_cap(self) -> None:
        """Cap MPS memory before the allocator initialises (first allocation).

        Set via env because PyTorch reads it once when the MPS allocator starts.
        `setdefault` so an explicit user override always wins.
        """
        if self._device_map != "mps" or self._mps_high_watermark_ratio <= 0:
            return
        import os

        os.environ.setdefault(
            "PYTORCH_MPS_HIGH_WATERMARK_RATIO",
            str(self._mps_high_watermark_ratio),
        )

    @staticmethod
    def _release_device_memory(torch) -> None:
        try:
            if torch.backends.mps.is_available() and hasattr(torch, "mps"):
                torch.mps.empty_cache()
            elif torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:  # noqa: BLE001 - best-effort cleanup, never fail a request
            pass
