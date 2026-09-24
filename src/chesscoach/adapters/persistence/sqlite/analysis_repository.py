import sqlite3
from datetime import UTC, datetime
from typing import Any

from chesscoach.adapters.persistence.sqlite.database import SqliteDatabase
from chesscoach.domain.entities import GameAnalysis, MoveAnalysis
from chesscoach.domain.value_objects import Color, Evaluation, MoveClass, Phase

_GAME_ANALYSIS_COLUMNS = (
    "game_id",
    "depth",
    "analyzed_at",
)
_INSERT_GAME_ANALYSIS = (
    f"INSERT OR REPLACE INTO game_analyses ({', '.join(_GAME_ANALYSIS_COLUMNS)}) "
    f"VALUES ({', '.join(f':{column}' for column in _GAME_ANALYSIS_COLUMNS)})"
)
_MOVE_ANALYSIS_COLUMNS = (
    "game_id",
    "ply",
    "color",
    "san",
    "fen_before",
    "phase",
    "eval_before_cp",
    "eval_before_mate",
    "eval_after_cp",
    "eval_after_mate",
    "best_move_san",
    "win_pct_loss",
    "move_class",
    "clock_seconds",
)
_INSERT_MOVE_ANALYSIS = (
    f"INSERT INTO move_analyses ({', '.join(_MOVE_ANALYSIS_COLUMNS)}) "
    f"VALUES ({', '.join(f':{column}' for column in _MOVE_ANALYSIS_COLUMNS)})"
)
_SELECT_GAME_ANALYSIS = (
    f"SELECT {', '.join(_GAME_ANALYSIS_COLUMNS)} FROM game_analyses WHERE game_id = ?"
)
_SELECT_MOVE_ANALYSES = (
    f"SELECT {', '.join(_MOVE_ANALYSIS_COLUMNS)} FROM move_analyses WHERE game_id = ? ORDER BY ply"
)
_SELECT_ANALYZED_IDS = "SELECT game_id FROM game_analyses"
_DELETE_MOVE_ANALYSES = "DELETE FROM move_analyses WHERE game_id = ?"


class SqliteAnalysisRepository:
    def __init__(self, db: SqliteDatabase) -> None:
        self._db = db

    def save(self, analysis: GameAnalysis) -> None:
        with self._db.connect() as conn:
            conn.execute(_DELETE_MOVE_ANALYSES, (analysis.game_id,))
            conn.execute(_INSERT_GAME_ANALYSIS, _game_analysis_to_row(analysis))
            conn.executemany(
                _INSERT_MOVE_ANALYSIS,
                (_move_analysis_to_row(analysis.game_id, move) for move in analysis.moves),
            )

    def get(self, game_id: str) -> GameAnalysis | None:
        with self._db.connect() as conn:
            game_row = conn.execute(_SELECT_GAME_ANALYSIS, (game_id,)).fetchone()
            if game_row is None:
                return None
            move_rows = conn.execute(_SELECT_MOVE_ANALYSES, (game_id,)).fetchall()
        return _to_game_analysis(game_row, move_rows)

    def analyzed_ids(self) -> set[str]:
        with self._db.connect() as conn:
            rows = conn.execute(_SELECT_ANALYZED_IDS).fetchall()
        return {row["game_id"] for row in rows}


def _game_analysis_to_row(analysis: GameAnalysis) -> dict[str, Any]:
    return {
        "game_id": analysis.game_id,
        "depth": analysis.depth,
        "analyzed_at": datetime.now(UTC).isoformat(),
    }


def _move_analysis_to_row(game_id: str, move: MoveAnalysis) -> dict[str, Any]:
    return {
        "game_id": game_id,
        "ply": move.ply,
        "color": move.color.value,
        "san": move.san,
        "fen_before": move.fen_before,
        "phase": move.phase.value,
        "eval_before_cp": move.eval_before.centipawns,
        "eval_before_mate": move.eval_before.mate_in,
        "eval_after_cp": move.eval_after.centipawns,
        "eval_after_mate": move.eval_after.mate_in,
        "best_move_san": move.best_move_san,
        "win_pct_loss": move.win_pct_loss,
        "move_class": move.move_class.value,
        "clock_seconds": move.clock_seconds,
    }


def _to_game_analysis(game_row: sqlite3.Row, move_rows: list[sqlite3.Row]) -> GameAnalysis:
    moves = tuple(_to_move_analysis(row) for row in move_rows)
    return GameAnalysis(
        game_id=game_row["game_id"],
        depth=game_row["depth"],
        moves=moves,
    )


def _to_move_analysis(row: sqlite3.Row) -> MoveAnalysis:
    return MoveAnalysis(
        ply=row["ply"],
        color=Color(row["color"]),
        san=row["san"],
        fen_before=row["fen_before"],
        phase=Phase(row["phase"]),
        eval_before=_evaluation(row["eval_before_cp"], row["eval_before_mate"]),
        eval_after=_evaluation(row["eval_after_cp"], row["eval_after_mate"]),
        best_move_san=row["best_move_san"],
        win_pct_loss=row["win_pct_loss"],
        move_class=MoveClass(row["move_class"]),
        clock_seconds=row["clock_seconds"],
    )


def _evaluation(centipawns: int | None, mate_in: int | None) -> Evaluation:
    return Evaluation(centipawns=centipawns, mate_in=mate_in)
