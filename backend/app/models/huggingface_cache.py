"""Read and delete a single repo in the local Hugging Face cache.

The one place that touches `huggingface_hub`'s cache layout, so the engine and
transcriber adapters don't each re-implement (and drift on) the scan/delete
logic. Defensive throughout: if the hub isn't installed or the scan fails, a
repo simply reports as "not downloaded" and a purge is a no-op — never an error.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepoCacheEntry:
    """A repo's footprint in the local cache (absent → downloaded=False)."""

    downloaded: bool
    path: str | None
    size_bytes: int


_ABSENT = RepoCacheEntry(downloaded=False, path=None, size_bytes=0)


def describe(repo_id: str) -> RepoCacheEntry:
    """Report whether `repo_id` is cached locally, where, and how big."""
    cache = _scan()
    if cache is None:
        return _ABSENT
    for repo in cache.repos:
        if repo.repo_id == repo_id:
            return RepoCacheEntry(
                downloaded=True,
                path=str(repo.repo_path),
                size_bytes=repo.size_on_disk,
            )
    return _ABSENT


def purge(repo_id: str) -> tuple[bool, int]:
    """Delete every cached revision of `repo_id`; return (found, freed_bytes)."""
    cache = _scan()
    if cache is None:
        return False, 0
    commit_hashes: list[str] = []
    freed = 0
    for repo in cache.repos:
        if repo.repo_id == repo_id:
            freed += repo.size_on_disk
            commit_hashes.extend(rev.commit_hash for rev in repo.revisions)
    if not commit_hashes:
        return False, 0
    cache.delete_revisions(*commit_hashes).execute()
    return True, freed


def _scan():
    """Scan the HF cache, or None if the hub is absent / the scan fails."""
    try:
        from huggingface_hub import scan_cache_dir
    except Exception:  # noqa: BLE001 - hub not installed: nothing is cached
        return None
    try:
        return scan_cache_dir()
    except Exception:  # noqa: BLE001 - missing/corrupt cache dir: treat as empty
        return None
