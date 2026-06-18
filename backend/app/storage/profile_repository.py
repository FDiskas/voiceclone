"""Persistence for VoiceProfile entities (SQLite metadata + on-disk audio)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ..domain.profile import VoiceProfile
from ..domain.values import Language, ProfileId, Transcript, VoiceName
from .database import Database


class ProfileRepository:
    """Reads and writes voice profiles. The audio bytes live as files; the
    row stores only the path, so the DB stays small."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def add(self, profile: VoiceProfile) -> None:
        with self._database.connect() as connection:
            connection.execute(
                """
                INSERT INTO profiles
                    (id, name, language, transcript, reference_audio_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    profile.id.value,
                    profile.name.value,
                    profile.language.code,
                    profile.transcript.value,
                    str(profile.reference_audio_path),
                    profile.created_at.isoformat(),
                ),
            )

    def list_all(self) -> list[VoiceProfile]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM profiles ORDER BY created_at DESC"
            ).fetchall()
        return [self._to_entity(row) for row in rows]

    def find(self, profile_id: ProfileId) -> VoiceProfile | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM profiles WHERE id = ?", (profile_id.value,)
            ).fetchone()
        return self._to_entity(row) if row else None

    def remove(self, profile_id: ProfileId) -> None:
        with self._database.connect() as connection:
            connection.execute("DELETE FROM profiles WHERE id = ?", (profile_id.value,))

    @staticmethod
    def _to_entity(row) -> VoiceProfile:
        return VoiceProfile(
            id=ProfileId(row["id"]),
            name=VoiceName(row["name"]),
            language=Language(row["language"]),
            transcript=Transcript(row["transcript"]),
            reference_audio_path=Path(row["reference_audio_path"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
