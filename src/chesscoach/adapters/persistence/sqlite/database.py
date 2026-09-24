import contextlib
import sqlite3
from collections.abc import Iterator
from pathlib import Path

# Append new migrations; never edit one that has shipped. Version = position in the list.
_MIGRATIONS = [
    """
    CREATE TABLE IF NOT EXISTS games (
        id TEXT PRIMARY KEY,
        url TEXT NOT NULL,
        played_at TEXT NOT NULL,
        time_class TEXT NOT NULL,
        time_control TEXT NOT NULL,
        rated INTEGER NOT NULL,
        white_username TEXT NOT NULL,
        white_rating INTEGER NOT NULL,
        black_username TEXT NOT NULL,
        black_rating INTEGER NOT NULL,
        user_color TEXT NOT NULL,
        user_username_lc TEXT NOT NULL,
        outcome TEXT NOT NULL,
        termination TEXT NOT NULL,
        eco TEXT,
        opening TEXT,
        pgn TEXT NOT NULL,
        accuracy_white REAL,
        accuracy_black REAL
    );
    CREATE INDEX IF NOT EXISTS games_user_played_at
        ON games(user_username_lc, played_at);

    CREATE TABLE IF NOT EXISTS sync_state (
        username_lc TEXT NOT NULL,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        synced_at TEXT NOT NULL,
        PRIMARY KEY(username_lc, year, month)
    );

    CREATE TABLE IF NOT EXISTS http_cache (
        url TEXT PRIMARY KEY,
        etag TEXT NOT NULL,
        body BLOB NOT NULL,
        stored_at TEXT NOT NULL
    );
    """,
]


class SqliteDatabase:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)

        with contextlib.closing(sqlite3.connect(path)) as conn:
            self._apply_migrations(conn)

    @staticmethod
    def _apply_migrations(conn: sqlite3.Connection) -> None:
        current_version: int = conn.execute("PRAGMA user_version").fetchone()[0]
        for version, migration_sql in enumerate(_MIGRATIONS, start=1):
            if version > current_version:
                conn.executescript(migration_sql)
                conn.execute(f"PRAGMA user_version = {version}")
        conn.commit()

    @contextlib.contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """A connection inside a transaction; commits on success, always closed."""
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()
