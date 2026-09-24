from dataclasses import dataclass

from chesscoach.adapters.persistence.sqlite.database import SqliteDatabase


@dataclass(frozen=True, slots=True)
class CachedEntry:
    etag: str
    body: bytes


class SqliteResponseCache:
    def __init__(self, db: SqliteDatabase) -> None:
        self._db = db

    def get(self, url: str) -> CachedEntry | None:
        with self._db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT etag, body FROM http_cache WHERE url = ?",
                (url,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return CachedEntry(etag=row[0], body=row[1])

    def put(self, url: str, etag: str, body: bytes) -> None:
        with self._db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO http_cache (url, etag, body, stored_at) "
                "VALUES (?, ?, ?, datetime('now'))",
                (url, etag, body),
            )
