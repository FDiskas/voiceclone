"""Engine-readiness reporting: the helpers and the HTTP endpoints."""

from fastapi.testclient import TestClient

from app.api.dependencies import get_voice_engine
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
