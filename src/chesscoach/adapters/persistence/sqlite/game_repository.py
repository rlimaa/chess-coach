import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from chesscoach.adapters.persistence.sqlite.database import SqliteDatabase
from chesscoach.domain.entities import Accuracies, Game, PlayerSide
from chesscoach.domain.value_objects import Color, Outcome, TimeClass, TimeControl

_COLUMNS = (
    "id",
    "url",
    "played_at",
    "time_class",
    "time_control",
    "rated",
    "white_username",
    "white_rating",
    "black_username",
    "black_rating",
    "user_color",
    "user_username_lc",
    "outcome",
    "termination",
    "eco",
    "opening",
    "pgn",
    "accuracy_white",
    "accuracy_black",
)
_INSERT = (
    f"INSERT OR IGNORE INTO games ({', '.join(_COLUMNS)}) "
    f"VALUES ({', '.join(f':{column}' for column in _COLUMNS)})"
)
_SELECT_BY_USER = (
    f"SELECT {', '.join(_COLUMNS)} FROM games WHERE user_username_lc = ? ORDER BY played_at"
)


class SqliteGameRepository:
    def __init__(self, db: SqliteDatabase) -> None:
        self._db = db

    def add(self, games: Iterable[Game]) -> int:
        with self._db.connect() as conn:
            return sum(conn.execute(_INSERT, _to_row(game)).rowcount for game in games)

    def games_of(self, username: str) -> list[Game]:
        with self._db.connect() as conn:
            rows = conn.execute(_SELECT_BY_USER, (username.lower(),)).fetchall()
        return [_to_game(row) for row in rows]


def _to_row(game: Game) -> dict[str, Any]:
    accuracies = game.accuracies
    return {
        "id": game.id,
        "url": game.url,
        "played_at": game.played_at.astimezone(UTC).isoformat(),
        "time_class": game.time_class.value,
        "time_control": game.time_control.raw,
        "rated": int(game.rated),
        "white_username": game.white.username,
        "white_rating": game.white.rating,
        "black_username": game.black.username,
        "black_rating": game.black.rating,
        "user_color": game.user_color.value,
        "user_username_lc": game.user.username.lower(),
        "outcome": game.outcome.value,
        "termination": game.termination,
        "eco": game.eco,
        "opening": game.opening,
        "pgn": game.pgn,
        "accuracy_white": accuracies.white if accuracies else None,
        "accuracy_black": accuracies.black if accuracies else None,
    }


def _to_game(row: sqlite3.Row) -> Game:
    has_accuracies = row["accuracy_white"] is not None and row["accuracy_black"] is not None
    return Game(
        id=row["id"],
        url=row["url"],
        played_at=datetime.fromisoformat(row["played_at"]),
        time_class=TimeClass(row["time_class"]),
        time_control=TimeControl.parse(row["time_control"]),
        rated=bool(row["rated"]),
        white=PlayerSide(row["white_username"], row["white_rating"]),
        black=PlayerSide(row["black_username"], row["black_rating"]),
        user_color=Color(row["user_color"]),
        outcome=Outcome(row["outcome"]),
        termination=row["termination"],
        eco=row["eco"],
        opening=row["opening"],
        pgn=row["pgn"],
        accuracies=(
            Accuracies(row["accuracy_white"], row["accuracy_black"]) if has_accuracies else None
        ),
    )
