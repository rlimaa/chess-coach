from chesscoach.application.dto import GameDetail, GameSummary
from chesscoach.application.errors import GameNotFoundError
from chesscoach.application.ports import AnalysisRepository, GameReplayer, GameRepository
from chesscoach.domain.value_objects import TimeClass


class RecentGames:
    def __init__(self, games: GameRepository, analyses: AnalysisRepository) -> None:
        self._games = games
        self._analyses = analyses

    def execute(
        self, username: str, *, time_class: TimeClass | None, limit: int, offset: int = 0
    ) -> list[GameSummary]:
        newest_first = [
            g
            for g in reversed(self._games.games_of(username))
            if time_class in (None, g.time_class)
        ]
        page = newest_first[offset : offset + limit]
        analyses = self._analyses.get_many(g.id for g in page)
        return [
            GameSummary(
                game=g,
                analyzed=g.id in analyses,
                accuracy=analyses[g.id].accuracy(g.user_color) if g.id in analyses else None,
            )
            for g in page
        ]


class ShowGame:
    def __init__(
        self, games: GameRepository, analyses: AnalysisRepository, replayer: GameReplayer
    ) -> None:
        self._games = games
        self._analyses = analyses
        self._replayer = replayer

    def execute(self, reference: str) -> GameDetail:
        game = self._games.find(reference)
        if game is None:
            raise GameNotFoundError(reference)
        return GameDetail(game, self._analyses.get(game.id), self._replayer.replay(game.pgn))
