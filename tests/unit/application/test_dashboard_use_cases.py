from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from chesscoach.application.dto import ReplayedGame
from chesscoach.application.errors import GameNotFoundError, PuzzleNotFoundError
from chesscoach.application.use_cases.build_insights import BuildInsights
from chesscoach.application.use_cases.puzzles import FindPuzzle
from chesscoach.application.use_cases.show_games import RecentGames, ShowGame
from chesscoach.domain.value_objects import Color, MoveClass, TimeClass
from tests.builders import make_analysis, make_game, make_move
from tests.fakes import (
    FakeClockReader,
    FakeReplayer,
    InMemoryAnalysisRepository,
    InMemoryGameRepository,
)

REPLAY = ReplayedGame(plies=(), final_fen="final")

T0 = datetime(2026, 9, 1, tzinfo=UTC)


def _repos() -> tuple[InMemoryGameRepository, InMemoryAnalysisRepository]:
    games, analyses = InMemoryGameRepository(), InMemoryAnalysisRepository()
    for i in range(5):
        games.add(
            [
                make_game(
                    id=f"b{i}",
                    url=f"https://chess.com/game/live/{i}",
                    played_at=T0 + timedelta(days=i),
                    time_class=TimeClass.BLITZ,
                    user_color=Color.WHITE,
                )
            ]
        )
    games.add([make_game(id="r0", time_class=TimeClass.RAPID)])
    blunder = make_move(
        color=Color.WHITE,
        san="a3",
        best_move_san="e4",
        move_class=MoveClass.BLUNDER,
        win_pct_loss=30.0,
    )
    analyses.save(make_analysis(make_game(id="b3"), make_move(color=Color.WHITE), blunder))
    return games, analyses


def test_build_insights_returns_insights_and_highlights_without_writing() -> None:
    games, analyses = _repos()
    build = BuildInsights(games, analyses, FakeClockReader({}), ZoneInfo("UTC"))

    bundle = build.execute("me", TimeClass.BLITZ)

    assert bundle is not None
    assert bundle.insights.overall.games == 5
    assert bundle.insights.analyzed_games == 1
    assert isinstance(bundle.highlights, tuple)
    assert build.execute("me", TimeClass.BULLET) is None


def test_recent_games_are_newest_first_with_analysis_status() -> None:
    games, analyses = _repos()

    recent = RecentGames(games, analyses).execute("me", time_class=TimeClass.BLITZ, limit=3)

    assert [s.game.id for s in recent] == ["b4", "b3", "b2"]
    assert [s.analyzed for s in recent] == [False, True, False]
    assert recent[1].accuracy is not None


def test_recent_games_can_page_and_include_every_time_class() -> None:
    games, analyses = _repos()

    page = RecentGames(games, analyses).execute("me", time_class=None, limit=2, offset=1)

    assert [s.game.id for s in page] == ["b3", "b2"]


def test_show_game_returns_the_analysis_when_there_is_one() -> None:
    games, analyses = _repos()
    show = ShowGame(games, analyses, FakeReplayer({}, default=REPLAY))

    detail = show.execute("3")
    assert detail.analysis is not None
    assert detail.replay.final_fen == "final"
    assert show.execute("b1").analysis is None
    with pytest.raises(GameNotFoundError):
        show.execute("nope")


def test_find_puzzle_rebuilds_it_from_the_analysis() -> None:
    games, analyses = _repos()
    find = FindPuzzle(games, analyses)

    puzzle = find.execute("b3:1")

    assert (puzzle.played_san, puzzle.solution_san) == ("a3", "e4")
    for missing in ("b3:0", "b1:0", "nope"):
        with pytest.raises(PuzzleNotFoundError):
            find.execute(missing)
