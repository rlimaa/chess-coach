from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from chesscoach.domain.entities import Game, PlayerSide
from chesscoach.domain.value_objects import Color, Outcome, TimeClass, TimeControl

_DEFAULT_GAME = Game(
    id="game-1",
    url="https://www.chess.com/game/live/1",
    played_at=datetime(2026, 9, 1, 12, 0, tzinfo=UTC),
    time_class=TimeClass.BLITZ,
    time_control=TimeControl.parse("180+2"),
    rated=True,
    white=PlayerSide(username="me", rating=1500),
    black=PlayerSide(username="rival", rating=1480),
    user_color=Color.WHITE,
    outcome=Outcome.WIN,
    termination="resigned",
    eco="C50",
    opening="Italian Game",
    pgn="1. e4 e5 *",
    accuracies=None,
)


def make_game(**overrides: Any) -> Game:
    return replace(_DEFAULT_GAME, **overrides)
