"""Best-effort capture of Hugging Face download progress.

`OmniVoice.from_pretrained` downloads weights through `huggingface_hub`, which
renders progress with its own `tqdm` bars. We don't control that call, so to
surface a real percentage we temporarily wrap the `update` method of the tqdm
class those downloads use, forwarding aggregate byte counts to a callback.

We patch the *class method in place* rather than rebinding per-module `tqdm`
names: huggingface_hub (>=1.0) imports its submodules lazily, so the modules
that actually create download bars (`file_download`, `_snapshot_download`) are
not yet in `sys.modules` when this hook installs — and `snapshot_download`
funnels every file's bytes through one shared bar (`_AggregatedTqdm` forwards
to it). Both the per-file bars and that shared bar are instances of
`huggingface_hub.utils.tqdm.tqdm`, so wrapping its `update` catches every byte
no matter when the modules load.

This is intentionally defensive: huggingface_hub may be absent, or a future
version may move things around. Any failure to hook leaves downloads working
exactly as before — the caller just won't get a fraction and shows an
indeterminate indicator instead.
"""

from __future__ import annotations

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
        # Force-import the submodule that defines the bar class (it loads
        # lazily, so it may not be in sys.modules yet) and grab the class.
        from huggingface_hub.utils.tqdm import tqdm as hf_tqdm
    except Exception:  # noqa: BLE001 - hub not installed / moved: skip silently
        yield
        return

    tracker = _ByteTracker(on_progress)
    restore = _patch_update(hf_tqdm, tracker)
    try:
        yield
    finally:
        restore()


_BYTE_UNIT = "B"


class _ByteTracker:
    """Aggregates download progress across every bar into one fraction.

    huggingface_hub may open one progress bar per file (older versions) or, with
    newer versions, a shared byte bar (`unit="B"`) alongside a "Fetching N
    files" *count* bar. Summing both mixes units (files + bytes) and pins the
    fraction near zero while the one large weights file downloads, so when any
    byte bar is active we report byte progress alone and ignore the count bars.
    Each bar's last `n` is retained after it closes so the total stays monotonic.
    """

    def __init__(self, on_progress: ProgressCallback) -> None:
        self._on_progress = on_progress
        self._lock = threading.Lock()
        self._bars: dict[int, _BarState] = {}

    def update(self, bar_id: int, n: int, total: int, unit: str) -> None:
        with self._lock:
            self._bars[bar_id] = _BarState(n=n, total=total, is_bytes=unit == _BYTE_UNIT)
            bars = list(self._bars.values())
        relevant = [b for b in bars if b.is_bytes] or bars
        downloaded = sum(b.n for b in relevant)
        total_sum = sum(b.total for b in relevant if b.total)
        self._on_progress(downloaded, total_sum)


class _BarState:
    """One tqdm bar's last-seen counts and whether it measures bytes."""

    __slots__ = ("n", "total", "is_bytes")

    def __init__(self, n: int, total: int, is_bytes: bool) -> None:
        self.n = n
        self.total = total
        self.is_bytes = is_bytes


def _patch_update(cls: type, tracker: _ByteTracker) -> Callable[[], None]:
    """Wrap `cls.update` to report byte progress; return a restore callable.

    `cls.update` is typically inherited from `tqdm.auto.tqdm` rather than
    defined on `cls` itself, so the restore deletes our override to fall back
    to the inherited method instead of pinning a copy onto the class.
    """
    original = cls.update
    had_own = "update" in cls.__dict__

    def update(self, n=1):  # noqa: ANN001 - mirror tqdm's signature
        result = original(self, n)
        try:
            tracker.update(
                id(self),
                int(self.n or 0),
                int(self.total or 0),
                getattr(self, "unit", "") or "",
            )
        except Exception:  # noqa: BLE001 - never let reporting break a download
            pass
        return result

    try:
        cls.update = update  # type: ignore[method-assign]
    except Exception:  # noqa: BLE001 - read-only class, etc.: leave downloads untouched
        return lambda: None

    def restore() -> None:
        try:
            if had_own:
                cls.update = original  # type: ignore[method-assign]
            else:
                del cls.update
        except Exception:  # noqa: BLE001
            pass

    return restore
