from dataclasses import dataclass

from chesscoach.domain.entities import Game, GameAnalysis
from chesscoach.domain.insights import Highlight
from chesscoach.domain.services.statistics import ResultSummary
from chesscoach.domain.value_objects import Color, Evaluation, TimeClass


@dataclass(frozen=True, slots=True, order=True)
class ArchiveMonth:
    year: int
    month: int

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"


@dataclass(frozen=True, slots=True)
class SyncReport:
    months_fetched: int
    games_fetched: int
    games_added: int


@dataclass(frozen=True, slots=True)
class TimeClassStats:
    summary: ResultSummary
    current_rating: int
    peak_rating: int


@dataclass(frozen=True, slots=True)
class OpeningStats:
    name: str
    summary: ResultSummary


@dataclass(frozen=True, slots=True)
class PlayerStats:
    username: str
    overall: ResultSummary
    by_color: dict[Color, ResultSummary]
    by_time_class: dict[TimeClass, TimeClassStats]
    openings: list[OpeningStats]


@dataclass(frozen=True, slots=True)
class Ply:
    index: int
    color: Color
    san: str
    uci: str
    fen_before: str
    clock_seconds: float | None


@dataclass(frozen=True, slots=True)
class ReplayedGame:
    plies: tuple[Ply, ...]
    final_fen: str


@dataclass(frozen=True, slots=True)
class EngineLine:
    evaluation: Evaluation
    best_move_uci: str | None
    best_move_san: str | None


@dataclass(frozen=True, slots=True)
class AnalyzeReport:
    analyzed: int
    still_pending: int


@dataclass(frozen=True, slots=True)
class GameReview:
    game: Game
    analysis: GameAnalysis


@dataclass(frozen=True, slots=True)
class WrittenReport:
    time_class: TimeClass
    games: int
    highlights: tuple[Highlight, ...]
    location: str
