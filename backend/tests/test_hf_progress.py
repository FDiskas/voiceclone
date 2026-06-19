"""The HF download-progress hook must capture real byte progress.

These run against the installed `huggingface_hub` tqdm class (no network): we
drive its `update()` the way `snapshot_download`'s shared bar does and assert
our callback sees the bytes. If huggingface_hub isn't installed the hook must
no-op cleanly.
"""

import pytest

from app.engine.hf_progress import capture_download_progress

hf_tqdm_mod = pytest.importorskip("huggingface_hub.utils.tqdm")
hf_tqdm = hf_tqdm_mod.tqdm


def test_captures_progress_from_shared_bar():
    seen: list[tuple[int, int]] = []
    with capture_download_progress(lambda d, t: seen.append((d, t))):
        # Mimic snapshot_download's single shared bytes bar.
        bar = hf_tqdm(total=100, unit="B", disable=False)
        bar.update(30)
        bar.update(70)
        bar.close()

    assert seen, "callback never fired — progress not captured"
    assert seen[-1] == (100, 100)
    # Monotonic, and the mid-download fraction was reported (not just the end).
    assert (30, 100) in seen


def test_restores_update_after_context():
    original = hf_tqdm.update
    with capture_download_progress(lambda d, t: None):
        assert hf_tqdm.update is not original
    # Inherited method restored, not pinned as an own-attribute copy.
    assert hf_tqdm.update is original
    assert "update" not in hf_tqdm.__dict__


def test_no_capture_outside_context_does_not_leak():
    calls: list[tuple[int, int]] = []
    with capture_download_progress(lambda d, t: calls.append((d, t))):
        pass
    # A bar created after the context must not invoke the stale callback.
    bar = hf_tqdm(total=10, disable=False)
    bar.update(10)
    bar.close()
    assert calls == []


def test_prefers_byte_bar_over_file_count_bar():
    """snapshot_download runs a 'Fetching N files' count bar *and* a byte bar.

    Summing them mixes units (files + bytes) and pins progress near 0% while the
    one big weights file downloads. When any byte bar is active we must report
    byte progress alone.
    """
    seen: list[tuple[int, int]] = []
    with capture_download_progress(lambda d, t: seen.append((d, t))):
        # snapshot_download creates the byte bar upfront, then the count bar.
        data = hf_tqdm(total=1000, unit="B", unit_scale=True, disable=False)
        files = hf_tqdm(total=13, disable=False)  # default unit = file count
        data.update(500)  # half the bytes…
        files.update(1)  # …only 1 of 13 files done
        data.update(500)
        files.update(12)
        data.close()
        files.close()

    # Final byte state, not 13/1013 (mixed) — the file bar is excluded.
    assert seen[-1] == (1000, 1000)
    # Mid-download we reported the byte fraction (500/1000), never files+bytes.
    assert (500, 1000) in seen
    # Every reading is a byte fraction (total 1000), never the file count (13).
    assert all(total == 1000 for _, total in seen if total)


def test_total_grows_with_aggregate_bar():
    """snapshot_download bumps `total` as files are discovered; we track it."""
    seen: list[tuple[int, int]] = []
    with capture_download_progress(lambda d, t: seen.append((d, t))):
        bar = hf_tqdm(total=50, unit="B", disable=False)
        bar.update(50)
        bar.total += 50  # second file discovered mid-download
        bar.refresh()
        bar.update(50)
        bar.close()
    assert seen[-1] == (100, 100)
