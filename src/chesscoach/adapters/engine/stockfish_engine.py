from pathlib import Path
from types import TracebackType

import chess
import chess.engine

from chesscoach.application.dto import EngineLine, LineMove, Variation
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
        if board.is_game_over():
            evaluation = self._terminal_evaluation(board)
            return EngineLine(evaluation, None, None)

        info = self._engine.analyse(board, chess.engine.Limit(depth=depth))
        best = info["pv"][0] if info.get("pv") else None
        return EngineLine(
            evaluation=_evaluation(info["score"].white()),
            best_move_uci=best.uci() if best else None,
            best_move_san=board.san(best) if best else None,
        )

    def _terminal_evaluation(self, board: chess.Board) -> Evaluation:
        if board.is_checkmate():
            winner_sign = -1 if board.turn is chess.WHITE else 1
            return Evaluation.mate(winner_sign)
        return Evaluation.cp(0)

    def variation(
        self, fen: str, depth: int, max_plies: int, first_move_san: str | None = None
    ) -> Variation:
        board = chess.Board(fen)
        moves: list[LineMove] = []
        if first_move_san is not None:
            move = board.parse_san(first_move_san)
            san = board.san(move)
            board.push(move)
            moves.append(LineMove(san, board.fen()))
        if board.is_game_over():
            evaluation = self._terminal_evaluation(board)
            return Variation(evaluation, tuple(moves))
        info = self._engine.analyse(board, chess.engine.Limit(depth=depth))
        evaluation = _evaluation(info["score"].white())
        for move in info.get("pv", []):
            if len(moves) >= max_plies:
                break
            san = board.san(move)
            board.push(move)
            moves.append(LineMove(san, board.fen()))
        return Variation(evaluation, tuple(moves))


def _evaluation(score: chess.engine.Score) -> Evaluation:
    mate = score.mate()
    return Evaluation.mate(mate) if mate is not None else Evaluation.cp(score.score(mate_score=0))
