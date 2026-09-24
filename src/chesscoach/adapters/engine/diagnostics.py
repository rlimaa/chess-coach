from dataclasses import dataclass
from pathlib import Path

import chess
import chess.engine


@dataclass(frozen=True, slots=True)
class EngineProbe:
    name: str
    best_move: str
    score_cp: int | None
    depth: int


def probe_engine(path: Path, depth: int) -> EngineProbe:
    if not path.exists():
        raise FileNotFoundError(f"Chess engine not found at {path}")

    board = chess.Board()
    with chess.engine.SimpleEngine.popen_uci(str(path)) as engine:
        info = engine.analyse(board, chess.engine.Limit(depth=depth))
        pv = info.get("pv", [])
        score = info.get("score")
        return EngineProbe(
            name=engine.id.get("name", "unknown"),
            best_move=board.san(pv[0]) if pv else "",
            score_cp=score.white().score() if score is not None else None,
            depth=info.get("depth", depth),
        )
