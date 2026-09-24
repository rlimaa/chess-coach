from collections.abc import Callable
from datetime import datetime

from chesscoach.application.dto import PuzzleResult
from chesscoach.application.ports import (
    AnalysisRepository,
    ChessRules,
    GameRepository,
    PuzzleAttempts,
)
from chesscoach.domain.puzzles import Attempt, Puzzle
from chesscoach.domain.services.puzzles import due_puzzles, puzzles_from
from chesscoach.domain.value_objects import TimeClass

Clock = Callable[[], datetime]


class NextPuzzles:
    def __init__(
        self,
        games: GameRepository,
        analyses: AnalysisRepository,
        attempts: PuzzleAttempts,
        clock: Clock,
    ) -> None:
        self._games = games
        self._analyses = analyses
        self._attempts = attempts
        self._clock = clock

    def execute(self, username: str, *, time_class: TimeClass | None, limit: int) -> list[Puzzle]:
        games = [g for g in self._games.games_of(username) if time_class in (None, g.time_class)]
        analyses = self._analyses.get_many(g.id for g in games)
        reviews = [(g, analyses[g.id]) for g in games if g.id in analyses]
        return due_puzzles(
            puzzles_from(reviews), self._attempts.all(), now=self._clock(), limit=limit
        )


class SolvePuzzle:
    def __init__(self, rules: ChessRules, attempts: PuzzleAttempts, clock: Clock) -> None:
        self._rules = rules
        self._attempts = attempts
        self._clock = clock

    def execute(self, puzzle: Puzzle, answer: str) -> PuzzleResult:
        san = self._rules.normalize_move(puzzle.fen, answer)
        if san is None:
            return PuzzleResult(False, False, None, puzzle.solution_san)
        correct = san == puzzle.solution_san
        self._attempts.record(Attempt(puzzle.id, self._clock(), solved=correct))
        return PuzzleResult(True, correct, san, puzzle.solution_san)
