from pathlib import Path
from types import TracebackType

import chess
import chess.engine

from chesscoach.application.dto import EngineLine
from chesscoach.domain.value_objects import Evaluation


class StockfishEngine:
    def __init__(self, path: Path, *, threads: int, hash_mb: int) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Chess engine not found at {path}")
        self._engine = chess.engine.SimpleEngine.popen_uci(str(path))
        self._engine.configure({"Threads": threads, "Hash": hash_mb})

    def __enter__(self) -> "StockfishEngine":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self._engine.quit()

    def evaluate(self, fen: str, depth: int) -> EngineLine:
        board = chess.Board(fen)
        if board.is_checkmate():
            winner_sign = -1 if board.turn is chess.WHITE else 1
            return EngineLine(Evaluation.mate(winner_sign), None, None)
        if board.is_game_over():
            return EngineLine(Evaluation.cp(0), None, None)

        info = self._engine.analyse(board, chess.engine.Limit(depth=depth))
        best = info["pv"][0] if info.get("pv") else None
        return EngineLine(
            evaluation=_evaluation(info["score"].white()),
            best_move_uci=best.uci() if best else None,
            best_move_san=board.san(best) if best else None,
        )


def _evaluation(score: chess.engine.Score) -> Evaluation:
    mate = score.mate()
    return Evaluation.mate(mate) if mate is not None else Evaluation.cp(score.score(mate_score=0))
