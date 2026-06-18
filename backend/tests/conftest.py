from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.engine.fake_engine import FakeVoiceEngine
from app.services.profile_service import ProfileService
from app.services.synthesis_service import SynthesisService
from app.storage.database import Database
from app.storage.profile_repository import ProfileRepository
from app.transcription.fake_transcriber import FakeTranscriber


def _fake_normalizer(source: Path, destination: Path) -> Path:
    """Skip real normalization in tests: just persist the bytes at the destination."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())
    return destination


@pytest.fixture
def fixed_clock():
    return lambda: datetime(2026, 6, 18, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def profile_service(tmp_path, fixed_clock) -> ProfileService:
    database = Database(tmp_path / "test.db")
    repository = ProfileRepository(database)
    return ProfileService(
        repository,
        audio_dir=tmp_path / "audio",
        transcriber=FakeTranscriber(),
        normalize=_fake_normalizer,
        clock=fixed_clock,
    )


@pytest.fixture
def synthesis_service(profile_service) -> SynthesisService:
    return SynthesisService(profile_service, FakeVoiceEngine())


@pytest.fixture
def transcription_service() -> "TranscriptionService":
    from app.services.transcription_service import TranscriptionService

    return TranscriptionService(FakeTranscriber(), normalize=_fake_normalizer)
