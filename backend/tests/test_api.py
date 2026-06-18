import pytest
from fastapi.testclient import TestClient

import struct

from app.api.dependencies import (
    get_profile_service,
    get_synthesis_service,
    get_transcription_service,
)
from app.main import create_app


@pytest.fixture
def client(profile_service, synthesis_service, transcription_service):
    app = create_app()
    app.dependency_overrides[get_profile_service] = lambda: profile_service
    app.dependency_overrides[get_synthesis_service] = lambda: synthesis_service
    app.dependency_overrides[get_transcription_service] = lambda: transcription_service
    return TestClient(app)


def _create_profile(client):
    return client.post(
        "/api/profiles",
        data={"name": "My Voice", "language": "en", "transcript": "Reference text."},
        files={"audio": ("recording.webm", b"fake-audio", "audio/webm")},
    )


def test_health_reports_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_then_list_profile(client):
    created = _create_profile(client)
    assert created.status_code == 201
    profile_id = created.json()["id"]

    listed = client.get("/api/profiles")
    assert [p["id"] for p in listed.json()] == [profile_id]


def test_create_profile_with_bad_language_returns_422(client):
    response = client.post(
        "/api/profiles",
        data={"name": "x", "language": "bogus!", "transcript": "t"},
        files={"audio": ("a.wav", b"data", "audio/wav")},
    )
    assert response.status_code == 422


def test_synthesize_returns_wav_audio(client):
    profile_id = _create_profile(client).json()["id"]

    response = client.post(
        f"/api/profiles/{profile_id}/speech", json={"text": "Hello there", "speed": 1.0}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content[:4] == b"RIFF"


def test_synthesize_unknown_profile_returns_404(client):
    response = client.post("/api/profiles/missing/speech", json={"text": "Hi"})
    assert response.status_code == 404


def test_create_profile_without_transcript_auto_transcribes(client):
    response = client.post(
        "/api/profiles",
        data={"name": "My Voice", "language": "en"},
        files={"audio": ("a.wav", b"data", "audio/wav")},
    )
    assert response.status_code == 201
    assert response.json()["transcript"]  # auto-filled, non-empty


def test_transcribe_endpoint_returns_text(client):
    response = client.post(
        "/api/transcribe",
        data={"language": "en"},
        files={"audio": ("clip.webm", b"data", "audio/webm")},
    )
    assert response.status_code == 200
    assert response.json()["text"]


def test_streaming_returns_length_prefixed_wav_frames(client):
    profile_id = _create_profile(client).json()["id"]

    two_sentences = ("word " * 40).strip() + ". " + ("alpha " * 40).strip() + "."
    response = client.post(
        f"/api/profiles/{profile_id}/speech/stream",
        json={"text": two_sentences},
    )
    assert response.status_code == 200

    frames = _parse_frames(response.content)
    assert len(frames) == 2
    assert all(frame[:4] == b"RIFF" for frame in frames)


def _parse_frames(payload: bytes) -> list[bytes]:
    frames, offset = [], 0
    while offset < len(payload):
        (length,) = struct.unpack_from(">I", payload, offset)
        offset += 4
        frames.append(payload[offset : offset + length])
        offset += length
    return frames
