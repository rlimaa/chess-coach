from typing import Protocol

from chesscoach.application.dto import EngineLine
from chesscoach.application.ports import PositionEngine


class EvaluationCache(Protocol):
    def get(self, fen: str, depth: int) -> EngineLine | None: ...

    def put(self, fen: str, depth: int, line: EngineLine) -> None: ...


class InMemoryEvaluationCache:
    def __init__(self) -> None:
        self._cache: dict[tuple[str, int], EngineLine] = {}

    def get(self, fen: str, depth: int) -> EngineLine | None:
        return self._cache.get((fen, depth))

    def put(self, fen: str, depth: int, line: EngineLine) -> None:
        self._cache[(fen, depth)] = line


class CachingEngine:
    def __init__(self, inner: PositionEngine, cache: EvaluationCache) -> None:
        self._inner = inner
        self._cache = cache

    def evaluate(self, fen: str, depth: int) -> EngineLine:
        cached = self._cache.get(fen, depth)
        if cached is not None:
            return cached

        line = self._inner.evaluate(fen, depth)
        self._cache.put(fen, depth, line)
        return line
