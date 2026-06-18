"""Use case: create and manage anonymous voice profiles."""

from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ..audio.converter import normalize_to_wav
from ..domain.errors import ProfileNotFoundError
from ..domain.profile import VoiceProfile
from ..domain.values import Language, ProfileId, Transcript, VoiceName
from ..storage.profile_repository import ProfileRepository
from ..transcription.base import Transcriber

AudioNormalizer = Callable[[Path, Path], Path]
Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProfileService:
    """Turns a raw recording + metadata into a persisted VoiceProfile."""

    def __init__(
        self,
        repository: ProfileRepository,
        audio_dir: Path,
        transcriber: Transcriber,
        normalize: AudioNormalizer = normalize_to_wav,
        clock: Clock = _utc_now,
    ) -> None:
        self._repository = repository
        self._audio_dir = audio_dir
        self._transcriber = transcriber
        self._normalize = normalize
        self._clock = clock

    def create(
        self,
        name: str,
        language: str,
        audio_bytes: bytes,
        original_filename: str,
        transcript: str | None = None,
    ) -> VoiceProfile:
        # Validate metadata first (cheap) before touching the filesystem.
        voice_name = VoiceName(name)
        voice_language = Language(language)
        profile_id = ProfileId.generate()

        reference_path = self._store_reference_audio(profile_id, audio_bytes, original_filename)
        voice_transcript = self._resolve_transcript(transcript, reference_path, voice_language)

        profile = VoiceProfile(
            id=profile_id,
            name=voice_name,
            language=voice_language,
            transcript=voice_transcript,
            reference_audio_path=reference_path,
            created_at=self._clock(),
        )
        self._repository.add(profile)
        return profile

    def list_profiles(self) -> list[VoiceProfile]:
        return self._repository.list_all()

    def get(self, profile_id: str) -> VoiceProfile:
        profile = self._repository.find(ProfileId(profile_id))
        if profile is None:
            raise ProfileNotFoundError(f"no profile with id '{profile_id}'")
        return profile

    def delete(self, profile_id: str) -> None:
        profile = self.get(profile_id)
        profile.reference_audio_path.unlink(missing_ok=True)
        self._repository.remove(profile.id)

    def _resolve_transcript(
        self, transcript: str | None, reference_path: Path, language: Language
    ) -> Transcript:
        if transcript and transcript.strip():
            return Transcript(transcript)
        # No transcript provided: auto-transcribe the stored reference audio.
        return Transcript(self._transcriber.transcribe(reference_path, language.code))

    def _store_reference_audio(
        self, profile_id: ProfileId, audio_bytes: bytes, original_filename: str
    ) -> Path:
        self._audio_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(original_filename).suffix or ".bin"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as raw:
            raw.write(audio_bytes)
            raw_path = Path(raw.name)
        try:
            destination = self._audio_dir / f"{profile_id.value}.wav"
            return self._normalize(raw_path, destination)
        finally:
            raw_path.unlink(missing_ok=True)
