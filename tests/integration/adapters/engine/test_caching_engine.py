from chesscoach.adapters.engine.caching import CachingEngine, InMemoryEvaluationCache
from chesscoach.application.dto import EngineLine
from chesscoach.domain.value_objects import Evaluation
from tests.fakes import FakeEngine

LINE = EngineLine(Evaluation.cp(20), "e2e4", "e4")


def test_repeated_positions_are_served_from_cache() -> None:
    inner = FakeEngine({"fen": LINE})
    engine = CachingEngine(inner, InMemoryEvaluationCache())

    assert engine.evaluate("fen", depth=12) == LINE
    assert engine.evaluate("fen", depth=12) == LINE
    assert inner.calls == [("fen", 12)]


def test_a_different_depth_is_evaluated_again() -> None:
    inner = FakeEngine({"fen": LINE})
    engine = CachingEngine(inner, InMemoryEvaluationCache())

    engine.evaluate("fen", depth=12)
    engine.evaluate("fen", depth=16)

    assert inner.calls == [("fen", 12), ("fen", 16)]
