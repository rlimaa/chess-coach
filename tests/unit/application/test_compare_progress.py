from datetime import UTC, datetime, timedelta

import pytest

from chesscoach.application.use_cases.compare_progress import CompareProgress
from chesscoach.domain.entities import Game, PlayerSide
from chesscoach.domain.value_objects import Color, MoveClass, Outcome, TimeClass, TimeControl
from tests.builders import make_analysis, make_game, make_move
from tests.fakes import FakeClockReader, InMemoryAnalysisRepository, InMemoryGameRepository

NOW = datetime(2026, 9, 24, 12, tzinfo=UTC)


def _game(gid: str, days_ago: float, rating: int, outcome: Outcome, pgn: str = "") -> Game:
    return make_game(
        id=gid,
        pgn=pgn,
        played_at=NOW - timedelta(days=days_ago),
        time_class=TimeClass.BLITZ,
        time_control=TimeControl.parse("300"),
        user_color=Color.WHITE,
        white=PlayerSide("me", rating),
        outcome=outcome,
        termination="timeout" if outcome is Outcome.LOSS else "resigned",
    )


def _use_case() -> CompareProgress:
    games, analyses = InMemoryGameRepository(), InMemoryAnalysisRepository()
    before = _game("before", 70, 1300, Outcome.WIN)
    prev_loss = _game("p1", 40, 1290, Outcome.LOSS, pgn="calm")
    prev_win = _game("p2", 35, 1300, Outcome.WIN, pgn="calm")
    cur_win = _game("c1", 10, 1320, Outcome.WIN, pgn="panic")
    cur_win2 = _game("c2", 2, 1340, Outcome.WIN, pgn="calm")
    games.add([before, prev_loss, prev_win, cur_win, cur_win2])
    analyses.save(
        make_analysis(
            cur_win,
            make_move(color=Color.WHITE, move_class=MoveClass.BLUNDER, win_pct_loss=20.0),
            make_move(color=Color.WHITE),
        )
    )
    clocks = FakeClockReader({"calm": [290.0, 280.0], "panic": [20.0, 280.0]})
    return CompareProgress(games, analyses, clocks, lambda: NOW)


def test_compares_the_last_period_with_the_one_before() -> None:
    report = _use_case().execute("me", TimeClass.BLITZ, days=30)

    current, previous = report.current, report.previous
    assert (current.games, current.score_pct) == (2, 100.0)
    assert (previous.games, previous.score_pct) == (2, 50.0)
    assert current.rating_change == 40
    assert previous.rating_change == 0
    assert current.time_trouble_pct == 50.0
    assert previous.losses_on_time_pct == 100.0


def test_engine_metrics_cover_analyzed_games_of_the_period() -> None:
    report = _use_case().execute("me", TimeClass.BLITZ, days=30)

    assert report.current.analyzed_games == 1
    assert report.current.serious_per_100 == pytest.approx(50.0)
    assert report.previous.accuracy is None
