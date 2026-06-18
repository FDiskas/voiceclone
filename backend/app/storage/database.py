"""SQLite connection management and schema bootstrap."""

from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
    id                   TEXT PRIMARY KEY,
    name                 TEXT NOT NULL,
    language             TEXT NOT NULL,
    transcript           TEXT NOT NULL,
    reference_audio_path TEXT NOT NULL,
    created_at           TEXT NOT NULL
);
"""


class Database:
    """Owns the SQLite file and hands out connections.

    A connection per operation keeps things simple and thread-safe enough for
    FastAPI's default threadpool; SQLite serializes writes internally.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(_SCHEMA)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection
