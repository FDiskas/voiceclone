"""The real OmniVoice adapter — the only module that imports `omnivoice`.

OmniVoice (https://github.com/k2-fsa/OmniVoice) is a zero-shot multilingual
TTS model. The model is loaded lazily on first use so the server can start
(and serve profile management) before the weights are resident in memory.
"""

from __future__ import annotations

import logging

from ..domain.errors import SynthesisError
from .base import SynthesisRequest, SynthesisResult

_OUTPUT_SAMPLE_RATE = 24_000
_logger = logging.getLogger(__name__)


class OmniVoiceEngine:
    """Wraps `omnivoice.OmniVoice` behind the VoiceEngine protocol."""

    def __init__(self, model_id: str, device_map: str, dtype: str, num_step: int = 32) -> None:
        self._model_id = model_id
        self._device_map = device_map
        self._dtype = dtype
        self._num_step = num_step
        self._model = None

    def _load(self):
        if self._model is not None:
            return self._model
        try:
            import torch
            from omnivoice import OmniVoice
        except ImportError as exc:  # pragma: no cover - depends on optional deps
            raise SynthesisError(
                "omnivoice is not installed. Run `pip install omnivoice` or use ENGINE=fake."
            ) from exc

        dtype = getattr(torch, self._dtype, torch.float32)
        _logger.info("Loading OmniVoice model %s on %s", self._model_id, self._device_map)
        self._model = OmniVoice.from_pretrained(
            self._model_id, device_map=self._device_map, dtype=dtype
        )
        return self._model

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        model = self._load()
        try:
            audio = model.generate(
                text=request.text,
                ref_audio=str(request.reference_audio_path),
                ref_text=request.reference_text,
                num_step=self._num_step,
                speed=request.speed,
            )
        except Exception as exc:  # noqa: BLE001 - surface any engine failure uniformly
            raise SynthesisError(f"OmniVoice failed to synthesize: {exc}") from exc

        return SynthesisResult(samples=audio[0], sample_rate=_OUTPUT_SAMPLE_RATE)
