import pytest

from chesscoach.application.errors import GameNotAnalyzedError, GameNotFoundError
from chesscoach.application.use_cases.review_game import ReviewGame
from chesscoach.domain.entities import GameAnalysis
from tests.builders import make_game
from tests.fakes import InMemoryAnalysisRepository, InMemoryGameRepository


def _review(analyzed: bool) -> ReviewGame:
    games, analyses = InMemoryGameRepository(), InMemoryAnalysisRepository()
    games.add([make_game(id="g1", url="https://www.chess.com/game/live/77")])
    if analyzed:
        analyses.save(GameAnalysis(game_id="g1", depth=12, moves=()))
    return ReviewGame(games, analyses)


def test_review_pairs_the_game_with_its_analysis() -> None:
    review = _review(analyzed=True).execute("77")

    assert review.game.id == "g1"
    assert review.analysis.depth == 12


def test_unknown_game_is_reported() -> None:
    with pytest.raises(GameNotFoundError):
        _review(analyzed=True).execute("nope")


def test_game_without_analysis_is_reported() -> None:
    with pytest.raises(GameNotAnalyzedError):
        _review(analyzed=False).execute("g1")
