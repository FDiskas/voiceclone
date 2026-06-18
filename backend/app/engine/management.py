"""Model management — an optional engine capability (ISP, like readiness).

Only an engine that downloads weights has a model to manage. Deleting it lets
the user reclaim disk and force a fresh download on the next warm-up. Engines
without a managed model (the fake engine) simply don't implement this.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class DeletedModel:
    """Outcome of removing a downloaded model from the local cache."""

    repo_id: str
    found: bool  # whether anything was actually cached before deletion
    freed_bytes: int


class ModelManagementUnsupported(RuntimeError):
    """Raised when the active engine has no downloadable model to manage."""


@runtime_checkable
class ManagedModelEngine(Protocol):
    """An engine whose downloaded weights can be deleted and re-fetched."""

    def delete_model(self) -> DeletedModel:
        ...


def is_manageable(engine: object) -> bool:
    return isinstance(engine, ManagedModelEngine)


def delete_model(engine: object) -> DeletedModel:
    if isinstance(engine, ManagedModelEngine):
        return engine.delete_model()
    raise ModelManagementUnsupported(
        "The active engine has no downloadable model to delete."
    )
