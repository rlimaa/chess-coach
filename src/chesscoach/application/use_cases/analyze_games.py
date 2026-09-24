from collections.abc import Callable

from chesscoach.application.dto import AnalyzeReport, EngineLine, Ply
from chesscoach.application.ports import (
    AnalysisRepository,
    GameReplayer,
    GameRepository,
    PositionEngine,
)
from chesscoach.domain.entities import Game, GameAnalysis, MoveAnalysis
from chesscoach.domain.services.classification import assess_move
from chesscoach.domain.services.phase_detection import detect_phase

ProgressCallback = Callable[[Game, int, int], None]


class AnalyzeGames:
    def __init__(
        self,
        games: GameRepository,
        analyses: AnalysisRepository,
        replayer: GameReplayer,
        engine: PositionEngine,
    ) -> None:
        self._games = games
        self._analyses = analyses
        self._replayer = replayer
        self._engine = engine

    def execute(
        self,
        username: str,
        *,
        limit: int,
        depth: int,
        on_progress: ProgressCallback | None = None,
    ) -> AnalyzeReport:
        pending = self._pending_newest_first(username)
        batch = pending[:limit]
        for position, game in enumerate(batch, start=1):
            self._analyses.save(self._analyze(game, depth))
            if on_progress:
                on_progress(game, position, len(batch))
        return AnalyzeReport(analyzed=len(batch), still_pending=len(pending) - len(batch))

    def _pending_newest_first(self, username: str) -> list[Game]:
        done = self._analyses.analyzed_ids()
        return [game for game in reversed(self._games.games_of(username)) if game.id not in done]

    def _analyze(self, game: Game, depth: int) -> GameAnalysis:
        replay = self._replayer.replay(game.pgn)
        fens = [ply.fen_before for ply in replay.plies] + [replay.final_fen]
        lines = [self._engine.evaluate(fen, depth) for fen in fens]
        moves = tuple(
            _move_analysis(ply, before, after)
            for ply, before, after in zip(replay.plies, lines, lines[1:], strict=False)
        )
        return GameAnalysis(game_id=game.id, depth=depth, moves=moves)


def _move_analysis(ply: Ply, before: EngineLine, after: EngineLine) -> MoveAnalysis:
    loss, move_class = assess_move(
        ply.color,
        before.evaluation,
        after.evaluation,
        played_best=ply.uci == before.best_move_uci,
    )
    return MoveAnalysis(
        ply=ply.index,
        color=ply.color,
        san=ply.san,
        fen_before=ply.fen_before,
        phase=detect_phase(ply.index, ply.fen_before),
        eval_before=before.evaluation,
        eval_after=after.evaluation,
        best_move_san=before.best_move_san,
        win_pct_loss=loss,
        move_class=move_class,
        clock_seconds=ply.clock_seconds,
    )
