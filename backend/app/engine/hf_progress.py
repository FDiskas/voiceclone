"""Best-effort capture of Hugging Face download progress.

`OmniVoice.from_pretrained` downloads weights through `huggingface_hub`, which
renders progress with its own `tqdm` bars. We don't control that call, so to
surface a real percentage we temporarily swap the `tqdm` class those modules
use for a subclass that forwards aggregate byte counts to a callback.

This is intentionally defensive: huggingface_hub may be absent, or a future
version may move things around. Any failure to hook leaves downloads working
exactly as before — the caller just won't get a fraction and shows an
indeterminate indicator instead.
"""

from __future__ import annotations

import sys
import threading
from contextlib import contextmanager
from typing import Callable, Iterator

# Called with (downloaded_bytes, total_bytes); total may be 0 when unknown.
ProgressCallback = Callable[[int, int], None]


@contextmanager
def capture_download_progress(on_progress: ProgressCallback) -> Iterator[None]:
    """Report aggregate HF download progress to `on_progress` while active.

    Yields immediately and never raises on hook failure — downloads proceed
    regardless; the callback simply may not fire.
    """
    try:
        import huggingface_hub.utils as hf_utils  # noqa: F401  (import side effect)
    except Exception:  # noqa: BLE001 - hub not installed / import error: skip silently
        yield
        return

    tracker = _ByteTracker(on_progress)
    patched = _install(tracker)
    try:
        yield
    finally:
        _restore(patched)


class _ByteTracker:
    """Aggregates byte counts across every download bar into one fraction.

    huggingface_hub opens one progress bar per file. We retain each bar's last
    `n` even after it closes so the total stays monotonic across the download.
    """

    def __init__(self, on_progress: ProgressCallback) -> None:
        self._on_progress = on_progress
        self._lock = threading.Lock()
        self._downloaded: dict[int, int] = {}
        self._total: dict[int, int] = {}

    def update(self, bar_id: int, n: int, total: int) -> None:
        with self._lock:
            self._downloaded[bar_id] = n
            if total:
                self._total[bar_id] = total
            downloaded = sum(self._downloaded.values())
            total_sum = sum(self._total.values())
        self._on_progress(downloaded, total_sum)


def _make_tracking_tqdm(base: type, tracker: _ByteTracker) -> type:
    """Build a tqdm subclass that reports byte progress to `tracker`."""

    class _TrackingTqdm(base):  # type: ignore[misc, valid-type]
        def update(self, n=1):  # noqa: ANN001 - mirror tqdm's signature
            result = super().update(n)
            try:
                tracker.update(id(self), int(self.n or 0), int(self.total or 0))
            except Exception:  # noqa: BLE001 - never let reporting break a download
                pass
            return result

    return _TrackingTqdm


def _install(tracker: _ByteTracker) -> list[tuple[object, str, object]]:
    """Swap the `tqdm` attribute on every loaded hub module that exposes one.

    Returns the list of (module, attr, original) so they can be restored.
    """
    patched: list[tuple[object, str, object]] = []
    for name, module in list(sys.modules.items()):
        if not name.startswith("huggingface_hub"):
            continue
        original = getattr(module, "tqdm", None)
        if isinstance(original, type):
            try:
                setattr(module, "tqdm", _make_tracking_tqdm(original, tracker))
                patched.append((module, "tqdm", original))
            except Exception:  # noqa: BLE001 - read-only module attr, etc.
                pass
    return patched


def _restore(patched: list[tuple[object, str, object]]) -> None:
    for module, attr, original in patched:
        try:
            setattr(module, attr, original)
        except Exception:  # noqa: BLE001
            pass
