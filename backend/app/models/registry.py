"""Gathers the active managed models so the UI can list/manage them uniformly."""

from __future__ import annotations

from collections.abc import Iterable

from .managed_model import DeletedModel, ManagedModel, ModelInfo


class UnknownModelError(KeyError):
    """Raised when a delete targets a model key the registry doesn't hold."""


class ModelRegistry:
    """A keyed view over the managed models that are currently active."""

    def __init__(self, models: Iterable[ManagedModel]) -> None:
        # Keyed by the cheap static `model_key`; last one wins on collision.
        self._by_key = {model.model_key: model for model in models}

    def list(self) -> list[ModelInfo]:
        return [model.model_info() for model in self._by_key.values()]

    def delete(self, key: str) -> DeletedModel:
        model = self._by_key.get(key)
        if model is None:
            raise UnknownModelError(key)
        return model.delete_model()
