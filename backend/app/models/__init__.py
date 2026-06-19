"""Managed downloadable models — inspect and delete the local weights.

A "managed model" is any component that downloads weights from Hugging Face
and can therefore report where they live on disk and delete them to reclaim
space. Both the voice engine (OmniVoice) and the transcriber (Whisper) qualify;
the fake implementations do not. The registry gathers whichever ones are
active so the UI can list and manage them uniformly.
"""

from .managed_model import DeletedModel, ManagedModel, ModelInfo, is_managed
from .registry import ModelRegistry, UnknownModelError

__all__ = [
    "DeletedModel",
    "ManagedModel",
    "ModelInfo",
    "ModelRegistry",
    "UnknownModelError",
    "is_managed",
]
