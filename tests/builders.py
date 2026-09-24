from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from chesscoach.domain.entities import Game, GameAnalysis, MoveAnalysis, PlayerSide
from chesscoach.domain.insights import StreakImpact, TimeClassInsights
from chesscoach.domain.services.statistics import ResultSummary
from chesscoach.domain.value_objects import (
    Color,
    Evaluation,
    MoveClass,
    Outcome,
    Phase,
    TimeClass,
    TimeControl,
)

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


_DEFAULT_MOVE = MoveAnalysis(
    ply=0,
    color=Color.WHITE,
    san="e4",
    fen_before="fen",
    phase=Phase.MIDDLEGAME,
    eval_before=Evaluation.cp(0),
    eval_after=Evaluation.cp(0),
    best_move_san="e4",
    win_pct_loss=0.0,
    move_class=MoveClass.BEST,
    clock_seconds=None,
)


def make_move(**overrides: Any) -> MoveAnalysis:
    return replace(_DEFAULT_MOVE, **overrides)


def make_analysis(game: Game, *moves: MoveAnalysis) -> GameAnalysis:
    numbered = tuple(replace(m, ply=i) if m.ply == 0 and i else m for i, m in enumerate(moves))
    return GameAnalysis(game_id=game.id, depth=12, moves=numbered)
