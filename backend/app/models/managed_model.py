"""The managed-model capability and its value objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ModelInfo:
    """Where a downloadable model's weights live and how much space they use.

    `path`/`size_bytes` are populated only when `downloaded` is true; an
    un-fetched model reports its identity (key, label, repo_id) with no path.
    """

    key: str  # stable id used by the API/UI, e.g. "voice", "transcription"
    label: str  # human-facing name, e.g. "Voice model"
    repo_id: str  # Hugging Face repo the weights come from
    downloaded: bool
    path: str | None
    size_bytes: int


@dataclass(frozen=True)
class DeletedModel:
    """Outcome of removing a downloaded model from the local cache."""

    key: str
    repo_id: str
    found: bool  # whether anything was actually cached before deletion
    freed_bytes: int


@runtime_checkable
class ManagedModel(Protocol):
    """A component whose downloaded weights can be inspected and deleted.

    `model_key` is a cheap static identifier (no disk access) so the registry
    can route a delete without scanning the cache for every model first.
    """

    model_key: str

    def model_info(self) -> ModelInfo:
        ...

    def delete_model(self) -> DeletedModel:
        ...


def is_managed(obj: object) -> bool:
    """Whether `obj` exposes the managed-model capability."""
    return isinstance(obj, ManagedModel)
