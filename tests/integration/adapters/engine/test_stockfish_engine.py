from collections.abc import Iterator
from pathlib import Path

import pytest

from chesscoach.adapters.engine.stockfish_engine import StockfishEngine
from chesscoach.domain.value_objects import Evaluation

STOCKFISH = Path("/usr/local/bin/stockfish")
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
MATE_IN_ONE = "6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1"
BLACK_IS_MATED = "3R2k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 1"
STALEMATE = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not STOCKFISH.exists(), reason="Stockfish binary not available"),
]


@pytest.fixture(scope="module")
def engine() -> Iterator[StockfishEngine]:
    with StockfishEngine(STOCKFISH, threads=1, hash_mb=16) as sf:
        yield sf


def test_evaluates_start_position_as_roughly_equal(engine: StockfishEngine) -> None:
    line = engine.evaluate(START, depth=8)

    assert line.evaluation.centipawns is not None
    assert abs(line.evaluation.centipawns) < 100
    assert line.best_move_uci is not None
    assert line.best_move_san


def test_finds_mate_in_one_from_whites_point_of_view(engine: StockfishEngine) -> None:
    line = engine.evaluate(MATE_IN_ONE, depth=8)

    assert line.evaluation == Evaluation.mate(1)
    assert (line.best_move_uci, line.best_move_san) == ("d1d8", "Rd8#")


def test_checkmated_position_is_won_for_the_mating_side_with_no_move(
    engine: StockfishEngine,
) -> None:
    line = engine.evaluate(BLACK_IS_MATED, depth=8)

    assert line.evaluation.mate_in is not None
    assert line.evaluation.mate_in > 0
    assert line.best_move_uci is None


def test_stalemate_is_a_draw_with_no_move(engine: StockfishEngine) -> None:
    line = engine.evaluate(STALEMATE, depth=8)

    assert line.evaluation == Evaluation.cp(0)
    assert line.best_move_uci is None
