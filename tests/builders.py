from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from chesscoach.domain.entities import Game, PlayerSide
from chesscoach.domain.insights import StreakImpact, TimeClassInsights
from chesscoach.domain.services.statistics import ResultSummary
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


def summary(wins: int = 0, draws: int = 0, losses: int = 0) -> ResultSummary:
    return ResultSummary(wins=wins, draws=draws, losses=losses)


_EVEN = ResultSummary(wins=50, draws=0, losses=50)

_DEFAULT_INSIGHTS = TimeClassInsights(
    time_class=TimeClass.BLITZ,
    overall=_EVEN,
    openings=(),
    losses_by_termination={},
    wins_by_termination={},
    clock=None,
    streaks=StreakImpact(
        fresh=_EVEN, after_win=_EVEN, after_loss=_EVEN, after_two_plus_losses=_EVEN
    ),
    by_session_position=(),
    by_day_part={},
    by_weekday=(),
    by_rating_gap=(),
    rating_by_month=(),
)


def make_insights(**overrides: Any) -> TimeClassInsights:
    return replace(_DEFAULT_INSIGHTS, **overrides)
