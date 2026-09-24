from datetime import UTC, datetime

from chesscoach.application.use_cases.puzzles import NextPuzzles, SolvePuzzle
from chesscoach.domain.entities import MoveAnalysis
from chesscoach.domain.puzzles import Attempt
from chesscoach.domain.value_objects import Color, MoveClass, TimeClass
from tests.builders import make_analysis, make_game, make_move
from tests.fakes import (
    FakeChessRules,
    InMemoryAnalysisRepository,
    InMemoryGameRepository,
    InMemoryPuzzleAttempts,
)

NOW = datetime(2026, 9, 24, 12, tzinfo=UTC)


def _blunder(fen: str) -> MoveAnalysis:
    return make_move(
        color=Color.WHITE,
        fen_before=fen,
        san="a3",
        best_move_san="Nxf4",
        move_class=MoveClass.BLUNDER,
        win_pct_loss=30.0,
    )


def _next(attempts: InMemoryPuzzleAttempts | None = None) -> NextPuzzles:
    games, analyses = InMemoryGameRepository(), InMemoryAnalysisRepository()
    blitz = make_game(id="b", time_class=TimeClass.BLITZ, user_color=Color.WHITE)
    rapid = make_game(id="r", time_class=TimeClass.RAPID, user_color=Color.WHITE)
    games.add([blitz, rapid])
    analyses.save(make_analysis(blitz, _blunder("blitz-fen")))
    analyses.save(make_analysis(rapid, _blunder("rapid-fen")))
    return NextPuzzles(games, analyses, attempts or InMemoryPuzzleAttempts(), lambda: NOW)


def test_next_puzzles_come_from_analyzed_games_of_the_time_class() -> None:
    puzzles = _next().execute("me", time_class=TimeClass.BLITZ, limit=5)

    assert [p.fen for p in puzzles] == ["blitz-fen"]


def test_recently_solved_puzzles_are_not_offered_again() -> None:
    attempts = InMemoryPuzzleAttempts()
    attempts.record(Attempt("b:0", NOW, solved=True))

    puzzles = _next(attempts).execute("me", time_class=None, limit=5)

    assert [p.id for p in puzzles] == ["r:0"]


def test_solving_records_the_attempt_and_compares_with_the_engine_move() -> None:
    attempts = InMemoryPuzzleAttempts()
    puzzle = _next().execute("me", time_class=TimeClass.BLITZ, limit=1)[0]
    solve = SolvePuzzle(FakeChessRules({"nxf4": "Nxf4", "a3": "a3"}), attempts, lambda: NOW)

    right = solve.execute(puzzle, "nxf4")
    wrong = solve.execute(puzzle, "a3")

    assert (right.legal, right.correct, right.answer_san) == (True, True, "Nxf4")
    assert (wrong.correct, wrong.solution_san) == (False, "Nxf4")
    assert attempts.all() == [Attempt("b:0", NOW, True), Attempt("b:0", NOW, False)]


def test_unreadable_answers_are_not_counted_as_attempts() -> None:
    attempts = InMemoryPuzzleAttempts()
    puzzle = _next().execute("me", time_class=None, limit=1)[0]

    result = SolvePuzzle(FakeChessRules({}), attempts, lambda: NOW).execute(puzzle, "Qz9")

    assert not result.legal
    assert attempts.all() == []
