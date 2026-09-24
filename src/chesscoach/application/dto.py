from dataclasses import dataclass
from datetime import date, datetime

from chesscoach.domain.entities import Game, GameAnalysis
from chesscoach.domain.insights import Highlight, TimeClassInsights
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


@dataclass(frozen=True, slots=True)
class PuzzleResult:
    legal: bool
    correct: bool
    answer_san: str | None
    solution_san: str


@dataclass(frozen=True, slots=True)
class PeriodMetrics:
    games: int
    score_pct: float
    rating_change: int | None
    time_trouble_pct: float | None
    losses_on_time_pct: float | None
    analyzed_games: int
    accuracy: float | None
    serious_per_100: float | None


@dataclass(frozen=True, slots=True)
class ProgressReport:
    time_class: TimeClass
    days: int
    current: PeriodMetrics
    previous: PeriodMetrics


@dataclass(frozen=True, slots=True)
class InsightsBundle:
    insights: TimeClassInsights
    highlights: tuple[Highlight, ...]


@dataclass(frozen=True, slots=True)
class GameSummary:
    game: Game
    analyzed: bool
    accuracy: float | None


@dataclass(frozen=True, slots=True)
class GameDetail:
    game: Game
    analysis: GameAnalysis | None
    replay: ReplayedGame


@dataclass(frozen=True, slots=True)
class TrainingPlan:
    markdown: str
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class GameFilter:
    time_class: TimeClass | None = None
    since: date | None = None

    def matches(self, game: Game) -> bool:
        return self.time_class in (None, game.time_class) and (
            self.since is None or game.played_at.date() >= self.since
        )


@dataclass(frozen=True, slots=True)
class LineMove:
    san: str
    fen_after: str


@dataclass(frozen=True, slots=True)
class Variation:
    """Engine line; the evaluation is White's, after the line's first move."""

    evaluation: Evaluation
    moves: tuple[LineMove, ...]


@dataclass(frozen=True, slots=True)
class LineSearch:
    depth: int
    max_plies: int


@dataclass(frozen=True, slots=True)
class PuzzleExplanation:
    best: Variation
    attempted: Variation | None
