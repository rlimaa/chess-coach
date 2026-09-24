from datetime import UTC, datetime
from pathlib import Path

from chesscoach.adapters.persistence.sqlite.database import SqliteDatabase
from chesscoach.adapters.persistence.sqlite.puzzle_attempts import SqlitePuzzleAttempts
from chesscoach.domain.puzzles import Attempt


def test_attempts_are_stored_and_returned_oldest_first(tmp_path: Path) -> None:
    attempts = SqlitePuzzleAttempts(SqliteDatabase(tmp_path / "coach.db"))
    later = Attempt("g1:4", datetime(2026, 9, 24, 12, tzinfo=UTC), solved=True)
    earlier = Attempt("g1:4", datetime(2026, 9, 20, 9, tzinfo=UTC), solved=False)

    attempts.record(later)
    attempts.record(earlier)

    assert attempts.all() == [earlier, later]
