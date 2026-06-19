"""Cooperative cancellation for long-running, CPU-bound work.

A worker thread can't be force-killed, so cancellation is cooperative: the work
(sentence-by-sentence synthesis, segment-by-segment transcription) polls a
`CancellationToken` at its loop boundaries and unwinds early when it's set. The
signal is flipped from another thread — an async request watcher (see
`api/cancellation.py`) sets it when the HTTP client goes away — so it's backed
by a `threading.Event`, which is safe to set and read across threads.
"""

from __future__ import annotations

import threading


class OperationCancelled(Exception):
    """Raised to unwind work whose `CancellationToken` was cancelled.

    Not a `DomainError`: it's a control-flow signal, not a user-correctable
    problem, so it isn't mapped to a 4xx by the domain error handler.
    """


class CancellationToken:
    """A thread-safe flag that running work polls to know it should stop."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()


def raise_if_cancelled(token: CancellationToken | None) -> None:
    """Stop work at a loop boundary if its (optional) token was cancelled."""
    if token is not None and token.cancelled:
        raise OperationCancelled()
