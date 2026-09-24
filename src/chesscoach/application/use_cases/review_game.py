from chesscoach.application.dto import GameReview
from chesscoach.application.errors import GameNotAnalyzedError, GameNotFoundError
from chesscoach.application.ports import AnalysisRepository, GameRepository


class ReviewGame:
    def __init__(self, games: GameRepository, analyses: AnalysisRepository) -> None:
        self._games = games
        self._analyses = analyses

    def execute(self, reference: str) -> GameReview:
        game = self._games.find(reference)
        if game is None:
            raise GameNotFoundError(reference)
        analysis = self._analyses.get(game.id)
        if analysis is None:
            raise GameNotAnalyzedError(game.id)
        return GameReview(game, analysis)
