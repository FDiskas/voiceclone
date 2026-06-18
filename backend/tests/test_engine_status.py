"""Engine-readiness reporting: the helpers and the HTTP endpoints."""

from fastapi.testclient import TestClient

from app.api.dependencies import get_voice_engine
from app.engine.management import DeletedModel, delete_model, is_manageable
from app.engine.management import ModelManagementUnsupported
from app.engine.readiness import (
    STATE_LOADING,
    STATE_READY,
    EngineStatus,
    status_of,
    warm_up,
)
from app.main import create_app


class _StubWarmable:
    """Minimal WarmableEngine: records warm_up and returns a canned status."""

    def __init__(self) -> None:
        self.warmed = 0
        self._status = EngineStatus(state=STATE_LOADING, message="Loading…", progress=0.5)

    def warm_up(self) -> None:
        self.warmed += 1

    def status(self) -> EngineStatus:
        return self._status


class _StubManaged(_StubWarmable):
    """A warmable engine that also supports model deletion."""

    def __init__(self) -> None:
        super().__init__()
        self.deleted = 0

    def delete_model(self) -> DeletedModel:
        self.deleted += 1
        return DeletedModel(repo_id="k2-fsa/OmniVoice", found=True, freed_bytes=12345)


def test_status_of_plain_engine_is_ready():
    # An engine without the warmable capability is reported ready.
    assert status_of(object()).ready


def test_warm_up_is_noop_for_plain_engine():
    warm_up(object())  # must not raise


def test_warm_up_and_status_delegate_to_warmable():
    engine = _StubWarmable()
    warm_up(engine)
    assert engine.warmed == 1
    assert status_of(engine).state == STATE_LOADING


def test_status_endpoint_reports_warmable_engine():
    engine = _StubWarmable()
    app = create_app()
    app.dependency_overrides[get_voice_engine] = lambda: engine
    client = TestClient(app)

    body = client.get("/api/engine/status").json()
    assert body == {
        "state": STATE_LOADING,
        "message": "Loading…",
        "progress": 0.5,
        "detail": None,
        "manageable": False,  # _StubWarmable has no delete_model
    }


def test_warmup_endpoint_triggers_warm_up():
    engine = _StubWarmable()
    app = create_app()
    app.dependency_overrides[get_voice_engine] = lambda: engine
    client = TestClient(app)

    response = client.post("/api/engine/warmup")
    assert response.status_code == 200
    assert engine.warmed == 1


def test_default_fake_engine_status_endpoint_is_ready():
    app = create_app()
    client = TestClient(app)
    body = client.get("/api/engine/status").json()
    assert body["state"] == STATE_READY
    # The fake engine has no downloadable model to manage.
    assert body["manageable"] is False


def test_status_endpoint_reports_manageable_for_managed_engine():
    engine = _StubManaged()
    app = create_app()
    app.dependency_overrides[get_voice_engine] = lambda: engine
    client = TestClient(app)

    assert client.get("/api/engine/status").json()["manageable"] is True


def test_delete_model_helper_requires_managed_engine():
    import pytest

    with pytest.raises(ModelManagementUnsupported):
        delete_model(object())
    assert is_manageable(object()) is False


def test_delete_model_endpoint_deletes_for_managed_engine():
    engine = _StubManaged()
    app = create_app()
    app.dependency_overrides[get_voice_engine] = lambda: engine
    client = TestClient(app)

    response = client.delete("/api/engine/model")
    assert response.status_code == 200
    assert response.json() == {
        "repo_id": "k2-fsa/OmniVoice",
        "found": True,
        "freed_bytes": 12345,
    }
    assert engine.deleted == 1


def test_delete_model_endpoint_409_for_unmanaged_engine():
    # The default fake engine isn't manageable -> conflict, not a crash.
    app = create_app()
    client = TestClient(app)
    assert client.delete("/api/engine/model").status_code == 409
