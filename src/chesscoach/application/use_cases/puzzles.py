from collections.abc import Callable
from datetime import datetime

from chesscoach.application.dto import LineSearch, PuzzleExplanation, PuzzleResult, Variation
from chesscoach.application.errors import (
    InvalidMoveError,
    PuzzleNotAttemptedError,
    PuzzleNotFoundError,
)
from chesscoach.application.ports import (
    AnalysisRepository,
    ChessRules,
    GameRepository,
    LineEngine,
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


class FindPuzzle:
    def __init__(self, games: GameRepository, analyses: AnalysisRepository) -> None:
        self._games = games
        self._analyses = analyses

    def execute(self, puzzle_id: str) -> Puzzle:
        return _find_puzzle(self._games, self._analyses, puzzle_id)


class ExplainPuzzle:
    def __init__(
        self,
        find: FindPuzzle,
        attempts: PuzzleAttempts,
        rules: ChessRules,
        engine: LineEngine,
        search: LineSearch,
    ) -> None:
        self._find = find
        self._attempts = attempts
        self._rules = rules
        self._engine = engine
        self._search = search

    def execute(self, puzzle_id: str, *, answer: str) -> PuzzleExplanation:
        puzzle = self._find.execute(puzzle_id)
        if not any(a.puzzle_id == puzzle_id for a in self._attempts.all()):
            raise PuzzleNotAttemptedError(puzzle_id)
        answer_san = self._rules.normalize_move(puzzle.fen, answer)
        if answer_san is None:
            raise InvalidMoveError(answer)
        best = self._line(puzzle.fen, puzzle.solution_san)
        attempted = (
            None if answer_san == puzzle.solution_san else self._line(puzzle.fen, answer_san)
        )
        return PuzzleExplanation(best, attempted)

    def _line(self, fen: str, first_move_san: str) -> Variation:
        return self._engine.variation(
            fen, self._search.depth, self._search.max_plies, first_move_san
        )


def _find_puzzle(games: GameRepository, analyses: AnalysisRepository, puzzle_id: str) -> Puzzle:
    game_id, _, _ = puzzle_id.rpartition(":")
    game = games.find(game_id) if game_id else None
    analysis = analyses.get(game.id) if game else None
    candidates = puzzles_from([(game, analysis)]) if game and analysis else []
    puzzle = next((p for p in candidates if p.id == puzzle_id), None)
    if puzzle is None:
        raise PuzzleNotFoundError(puzzle_id)
    return puzzle
