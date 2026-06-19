"""The model registry and the Hugging Face cache helper."""

import pytest

from app.models import ModelInfo, ModelRegistry, UnknownModelError
from app.models.managed_model import DeletedModel
from app.models import huggingface_cache as hf_cache


class _FakeModel:
    """A managed model that records deletion without touching disk."""

    def __init__(self, key: str, downloaded: bool = True) -> None:
        self.model_key = key
        self._downloaded = downloaded
        self.deleted = 0

    def model_info(self) -> ModelInfo:
        return ModelInfo(
            key=self.model_key,
            label=self.model_key.title(),
            repo_id=f"org/{self.model_key}",
            downloaded=self._downloaded,
            path=f"/cache/{self.model_key}" if self._downloaded else None,
            size_bytes=100 if self._downloaded else 0,
        )

    def delete_model(self) -> DeletedModel:
        self.deleted += 1
        return DeletedModel(key=self.model_key, repo_id=f"org/{self.model_key}", found=True, freed_bytes=100)


def test_lists_every_registered_model():
    registry = ModelRegistry([_FakeModel("voice"), _FakeModel("transcription")])
    keys = [info.key for info in registry.list()]
    assert keys == ["voice", "transcription"]


def test_delete_routes_to_the_matching_model():
    voice, transcription = _FakeModel("voice"), _FakeModel("transcription")
    registry = ModelRegistry([voice, transcription])

    result = registry.delete("transcription")

    assert result.key == "transcription"
    assert transcription.deleted == 1
    assert voice.deleted == 0


def test_delete_unknown_key_raises():
    registry = ModelRegistry([_FakeModel("voice")])
    with pytest.raises(UnknownModelError):
        registry.delete("nope")


# --- huggingface_cache: graceful + correct against a fake scan -------------


class _FakeRevision:
    def __init__(self, commit_hash: str) -> None:
        self.commit_hash = commit_hash


class _FakeRepo:
    def __init__(self, repo_id: str, path: str, size: int, hashes: list[str]) -> None:
        self.repo_id = repo_id
        self.repo_path = path
        self.size_on_disk = size
        self.revisions = [_FakeRevision(h) for h in hashes]


class _FakeCache:
    def __init__(self, repos: list[_FakeRepo]) -> None:
        self.repos = repos
        self.deleted: list[str] = []

    def delete_revisions(self, *hashes: str):
        cache = self

        class _Strategy:
            def execute(self) -> None:
                cache.deleted.extend(hashes)

        return _Strategy()


def test_describe_reports_cached_repo(monkeypatch):
    repo = _FakeRepo("org/voice", "/cache/voice", 4096, ["abc"])
    monkeypatch.setattr(hf_cache, "_scan", lambda: _FakeCache([repo]))

    entry = hf_cache.describe("org/voice")

    assert entry.downloaded is True
    assert entry.path == "/cache/voice"
    assert entry.size_bytes == 4096


def test_describe_absent_repo_is_not_downloaded(monkeypatch):
    monkeypatch.setattr(hf_cache, "_scan", lambda: _FakeCache([]))
    assert hf_cache.describe("org/missing").downloaded is False


def test_describe_no_hub_is_graceful(monkeypatch):
    monkeypatch.setattr(hf_cache, "_scan", lambda: None)
    assert hf_cache.describe("org/voice") == hf_cache._ABSENT


def test_purge_deletes_all_revisions_and_reports_freed(monkeypatch):
    repo = _FakeRepo("org/voice", "/cache/voice", 4096, ["abc", "def"])
    cache = _FakeCache([repo])
    monkeypatch.setattr(hf_cache, "_scan", lambda: cache)

    found, freed = hf_cache.purge("org/voice")

    assert found is True
    assert freed == 4096
    assert cache.deleted == ["abc", "def"]


def test_purge_absent_repo_is_noop(monkeypatch):
    cache = _FakeCache([])
    monkeypatch.setattr(hf_cache, "_scan", lambda: cache)
    assert hf_cache.purge("org/missing") == (False, 0)
    assert cache.deleted == []
