from datetime import datetime

from chesscoach.adapters.persistence.sqlite.database import SqliteDatabase
from chesscoach.domain.puzzles import Attempt

_INSERT = (
    "INSERT INTO puzzle_attempts (puzzle_id, attempted_at, solved) "
    "VALUES (:puzzle_id, :attempted_at, :solved)"
)
_SELECT = "SELECT puzzle_id, attempted_at, solved FROM puzzle_attempts ORDER BY attempted_at"


class SqlitePuzzleAttempts:
    def __init__(self, db: SqliteDatabase) -> None:
        self._db = db

    def record(self, attempt: Attempt) -> None:
        with self._db.connect() as conn:
            conn.execute(
                _INSERT,
                {
                    "puzzle_id": attempt.puzzle_id,
                    "attempted_at": attempt.attempted_at.isoformat(),
                    "solved": 1 if attempt.solved else 0,
                },
            )

    def all(self) -> list[Attempt]:
        with self._db.connect() as conn:
            rows = conn.execute(_SELECT).fetchall()
        return [
            Attempt(
                puzzle_id=row["puzzle_id"],
                attempted_at=datetime.fromisoformat(row["attempted_at"]),
                solved=bool(row["solved"]),
            )
            for row in rows
        ]
