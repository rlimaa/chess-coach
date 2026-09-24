import sqlite3
from typing import Any

from chesscoach.adapters.persistence.sqlite.database import SqliteDatabase
from chesscoach.application.dto import EngineLine
from chesscoach.domain.value_objects import Evaluation

_COLUMNS = (
    "fen",
    "depth",
    "cp",
    "mate",
    "best_move_uci",
    "best_move_san",
)
_INSERT = (
    f"INSERT OR REPLACE INTO engine_cache ({', '.join(_COLUMNS)}) "
    f"VALUES ({', '.join(f':{column}' for column in _COLUMNS)})"
)
_SELECT = (
    "SELECT cp, mate, best_move_uci, best_move_san FROM engine_cache WHERE fen = ? AND depth = ?"
)


class SqliteEvaluationCache:
    def __init__(self, db: SqliteDatabase) -> None:
        self._db = db

    def get(self, fen: str, depth: int) -> EngineLine | None:
        with self._db.connect() as conn:
            row = conn.execute(_SELECT, (fen, depth)).fetchone()
        if row is None:
            return None
        return _to_engine_line(row)

    def put(self, fen: str, depth: int, line: EngineLine) -> None:
        with self._db.connect() as conn:
            conn.execute(_INSERT, _to_row(fen, depth, line))


def _to_row(fen: str, depth: int, line: EngineLine) -> dict[str, Any]:
    return {
        "fen": fen,
        "depth": depth,
        "cp": line.evaluation.centipawns,
        "mate": line.evaluation.mate_in,
        "best_move_uci": line.best_move_uci,
        "best_move_san": line.best_move_san,
    }


def _to_engine_line(row: sqlite3.Row) -> EngineLine:
    return EngineLine(
        evaluation=Evaluation(centipawns=row["cp"], mate_in=row["mate"]),
        best_move_uci=row["best_move_uci"],
        best_move_san=row["best_move_san"],
    )
