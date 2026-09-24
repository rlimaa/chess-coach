from datetime import UTC, datetime

import pytest

from chesscoach.application.dto import LineMove, LineSearch, Variation
from chesscoach.application.errors import InvalidMoveError, PuzzleNotAttemptedError
from chesscoach.application.use_cases.puzzles import ExplainPuzzle, FindPuzzle
from chesscoach.domain.puzzles import Attempt
from chesscoach.domain.value_objects import Color, Evaluation, MoveClass
from tests.builders import make_analysis, make_game, make_move
from tests.fakes import (
    FakeChessRules,
    FakeLineEngine,
    InMemoryAnalysisRepository,
    InMemoryGameRepository,
    InMemoryPuzzleAttempts,
)

BEST = Variation(Evaluation.cp(250), (LineMove("Nxf4", "f1"), LineMove("gxf4", "f2")))
ATTEMPTED = Variation(Evaluation.cp(-120), (LineMove("Rh7+", "r1"), LineMove("Kg8", "r2")))
RULES = FakeChessRules({"Nxf4": "Nxf4", "g1f4": "Nxf4", "Rh7+": "Rh7+"})


def _explain(attempted: bool = True) -> tuple[ExplainPuzzle, FakeLineEngine]:
    games, analyses, attempts = (
        InMemoryGameRepository(),
        InMemoryAnalysisRepository(),
        InMemoryPuzzleAttempts(),
    )
    game = make_game(id="g", user_color=Color.WHITE)
    games.add([game])
    blunder = make_move(
        color=Color.WHITE,
        fen_before="puzzle-fen",
        san="Ng5",
        best_move_san="Nxf4",
        move_class=MoveClass.BLUNDER,
        win_pct_loss=30.0,
    )
    analyses.save(make_analysis(game, blunder))
    if attempted:
        attempts.record(Attempt("g:0", datetime(2026, 9, 24, tzinfo=UTC), solved=False))
    engine = FakeLineEngine({"Nxf4": BEST, "Rh7+": ATTEMPTED})
    explain = ExplainPuzzle(FindPuzzle(games, analyses), attempts, RULES, engine, LineSearch(18, 8))
    return explain, engine


def test_a_wrong_answer_shows_the_best_line_and_the_line_after_the_attempt() -> None:
    explain, engine = _explain()

    explanation = explain.execute("g:0", answer="Rh7+")

    assert (explanation.best, explanation.attempted) == (BEST, ATTEMPTED)
    assert engine.calls == [("puzzle-fen", "Nxf4"), ("puzzle-fen", "Rh7+")]


def test_a_correct_answer_in_any_notation_shows_only_the_best_line() -> None:
    explain, engine = _explain()

    explanation = explain.execute("g:0", answer="g1f4")

    assert explanation.attempted is None
    assert engine.calls == [("puzzle-fen", "Nxf4")]


def test_the_solution_is_not_revealed_before_an_attempt() -> None:
    explain, engine = _explain(attempted=False)

    with pytest.raises(PuzzleNotAttemptedError):
        explain.execute("g:0", answer="Rh7+")
    assert engine.calls == []


def test_an_illegal_answer_is_rejected() -> None:
    explain, engine = _explain()

    with pytest.raises(InvalidMoveError):
        explain.execute("g:0", answer="Qz9")
    assert engine.calls == []
