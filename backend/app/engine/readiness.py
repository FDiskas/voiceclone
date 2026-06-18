"""Engine readiness — a capability some engines have, kept off `VoiceEngine`.

Loading a multi-gigabyte model (and downloading it on first run) is a concern
of the *real* engine only; the fake engine is always ready. Rather than burden
the core `VoiceEngine` protocol with lifecycle methods every implementation
must satisfy (ISP), readiness is an optional, separately-typed capability.

Callers use `warm_up` / `status_of`, which degrade gracefully: an engine that
isn't warmable is simply reported as ready.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable

# Lifecycle states an engine moves through while becoming usable.
STATE_IDLE = "idle"  # warm-up not started yet
STATE_DOWNLOADING = "downloading"  # fetching weights (first run)
STATE_LOADING = "loading"  # weights present; loading into memory / device
STATE_READY = "ready"  # synthesis can proceed immediately
STATE_ERROR = "error"  # warm-up failed; `detail` explains why


@dataclass(frozen=True)
class EngineStatus:
    """A point-in-time snapshot of an engine's readiness."""

    state: str
    message: str
    # Download/load completion in [0, 1] when known, else None (indeterminate).
    progress: Optional[float] = None
    # Human-readable error text when `state == STATE_ERROR`.
    detail: Optional[str] = None

    @property
    def ready(self) -> bool:
        return self.state == STATE_READY


@runtime_checkable
class WarmableEngine(Protocol):
    """An engine that loads heavy resources and can report its progress."""

    def warm_up(self) -> None:
        """Begin loading resources (idempotent, non-blocking)."""

    def status(self) -> EngineStatus:
        ...


def warm_up(engine: object) -> None:
    """Kick off loading if the engine supports it; otherwise a no-op."""
    if isinstance(engine, WarmableEngine):
        engine.warm_up()


def status_of(engine: object) -> EngineStatus:
    """Report engine readiness; engines without the capability are ready."""
    if isinstance(engine, WarmableEngine):
        return engine.status()
    return EngineStatus(state=STATE_READY, message="Engine ready.", progress=1.0)
