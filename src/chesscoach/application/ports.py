from collections.abc import Iterable, Sequence
from typing import Protocol

from chesscoach.application.dto import ArchiveMonth, EngineLine, ReplayedGame, TrainingPlan
from chesscoach.domain.entities import Game, GameAnalysis
from chesscoach.domain.insights import Highlight, TimeClassInsights
from chesscoach.domain.puzzles import Attempt
from chesscoach.domain.value_objects import Color


class GameSource(Protocol):
    def archive_months(self, username: str) -> Sequence[ArchiveMonth]: ...

    def games_in_month(self, username: str, month: ArchiveMonth) -> Sequence[Game]: ...


class GameRepository(Protocol):
    def add(self, games: Iterable[Game]) -> int:
        """Store games, ignoring ones already stored. Returns how many were new."""
        ...

    def games_of(self, username: str) -> Sequence[Game]:
        """All stored games of a player, oldest first."""
        ...

    def find(self, reference: str) -> Game | None:
        """By game id, full URL, or the numeric id at the end of the URL."""
        ...


class SyncStateRepository(Protocol):
    def synced_months(self, username: str) -> set[ArchiveMonth]: ...

    def mark_synced(self, username: str, month: ArchiveMonth) -> None: ...


class GameReplayer(Protocol):
    def replay(self, pgn: str) -> ReplayedGame: ...


class PositionEngine(Protocol):
    def evaluate(self, fen: str, depth: int) -> EngineLine: ...


class AnalysisRepository(Protocol):
    def save(self, analysis: GameAnalysis) -> None: ...

    def get(self, game_id: str) -> GameAnalysis | None: ...

    def analyzed_ids(self) -> set[str]: ...

    def get_many(self, game_ids: Iterable[str]) -> dict[str, GameAnalysis]: ...


class ClockReader(Protocol):
    def clocks(self, pgn: str) -> Sequence[float]:
        """Remaining clock after each ply, in order, starting with White."""
        ...


class ReportWriter(Protocol):
    def write(
        self, username: str, insights: TimeClassInsights, highlights: Sequence[Highlight]
    ) -> str:
        """Persist the report and return where it can be found."""
        ...


class ChessRules(Protocol):
    def normalize_move(self, fen: str, text: str) -> str | None:
        """SAN of the move the text describes (SAN or UCI), or None if illegal/unreadable."""
        ...

    def render(self, fen: str, perspective: Color) -> str: ...


class PuzzleAttempts(Protocol):
    def record(self, attempt: Attempt) -> None: ...

    def all(self) -> list[Attempt]:
        """Every attempt, oldest first."""
        ...


class TrainingPlanSource(Protocol):
    def current(self) -> TrainingPlan | None: ...
