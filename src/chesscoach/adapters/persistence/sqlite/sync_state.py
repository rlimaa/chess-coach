from chesscoach.adapters.persistence.sqlite.database import SqliteDatabase
from chesscoach.application.dto import ArchiveMonth


class SqliteSyncState:
    def __init__(self, db: SqliteDatabase) -> None:
        self._db = db

    def synced_months(self, username: str) -> set[ArchiveMonth]:
        username_lc = username.lower()
        with self._db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT year, month FROM sync_state WHERE username_lc = ? ORDER BY year, month",
                (username_lc,),
            )
            return {ArchiveMonth(row[0], row[1]) for row in cursor.fetchall()}

    def mark_synced(self, username: str, month: ArchiveMonth) -> None:
        username_lc = username.lower()
        with self._db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO sync_state "
                "(username_lc, year, month, synced_at) "
                "VALUES (?, ?, ?, datetime('now'))",
                (username_lc, month.year, month.month),
            )
