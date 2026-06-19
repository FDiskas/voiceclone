"""The /api/models endpoints: list managed models and delete one by key."""

from fastapi.testclient import TestClient

from app.api.dependencies import get_model_registry
from app.main import create_app
from app.models import ModelRegistry, ModelInfo
from app.models.managed_model import DeletedModel


class _StubModel:
    def __init__(self, key: str) -> None:
        self.model_key = key
        self.deleted = 0

    def model_info(self) -> ModelInfo:
        return ModelInfo(
            key=self.model_key,
            label="Voice model",
            repo_id="k2-fsa/OmniVoice",
            downloaded=True,
            path="/cache/models--k2-fsa--OmniVoice",
            size_bytes=4096,
        )

    def delete_model(self) -> DeletedModel:
        self.deleted += 1
        return DeletedModel(key=self.model_key, repo_id="k2-fsa/OmniVoice", found=True, freed_bytes=4096)


def _client_with(registry: ModelRegistry) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_model_registry] = lambda: registry
    return TestClient(app)


def test_list_models_returns_path_and_size():
    client = _client_with(ModelRegistry([_StubModel("voice")]))

    body = client.get("/api/models").json()

    assert body == [
        {
            "key": "voice",
            "label": "Voice model",
            "repo_id": "k2-fsa/OmniVoice",
            "downloaded": True,
            "path": "/cache/models--k2-fsa--OmniVoice",
            "size_bytes": 4096,
        }
    ]


def test_delete_model_by_key():
    model = _StubModel("voice")
    client = _client_with(ModelRegistry([model]))

    response = client.delete("/api/models/voice")

    assert response.status_code == 200
    assert response.json() == {
        "key": "voice",
        "repo_id": "k2-fsa/OmniVoice",
        "found": True,
        "freed_bytes": 4096,
    }
    assert model.deleted == 1


def test_delete_unknown_model_is_404():
    client = _client_with(ModelRegistry([_StubModel("voice")]))
    assert client.delete("/api/models/transcription").status_code == 404


def test_default_fake_engine_has_no_managed_models():
    # Fake engine + fake transcriber → empty list, not an error.
    client = TestClient(create_app())
    assert client.get("/api/models").json() == []
