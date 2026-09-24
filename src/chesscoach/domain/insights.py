from dataclasses import dataclass
from enum import StrEnum

from chesscoach.domain.services.statistics import ResultSummary
from chesscoach.domain.value_objects import Color, Phase, TimeClass


class DayPart(StrEnum):
    NIGHT = "night (00-06)"
    MORNING = "morning (06-12)"
    AFTERNOON = "afternoon (12-18)"
    EVENING = "evening (18-24)"


@dataclass(frozen=True, slots=True)
class OpeningRecord:
    color: Color
    family: str
    summary: ResultSummary


@dataclass(frozen=True, slots=True)
class StreakImpact:
    """Score depending on the previous game of the same sitting."""

    fresh: ResultSummary
    after_win: ResultSummary
    after_loss: ResultSummary
    after_two_plus_losses: ResultSummary


@dataclass(frozen=True, slots=True)
class LabelledSummary:
    label: str
    summary: ResultSummary


@dataclass(frozen=True, slots=True)
class RatingGapBucket:
    label: str
    summary: ResultSummary
    expected_score_pct: float


@dataclass(frozen=True, slots=True)
class ClockProfile:
    games: int
    in_trouble: ResultSummary
    not_in_trouble: ResultSummary
    losses: int
    losses_on_time: int


@dataclass(frozen=True, slots=True)
class MonthRating:
    year: int
    month: int
    rating: int
    games: int


@dataclass(frozen=True, slots=True)
class Highlight:
    severity: float
    text: str
    strength: bool = False


@dataclass(frozen=True, slots=True)
class MomentRef:
    game_url: str
    ply: int
    san: str
    best_move_san: str | None


@dataclass(frozen=True, slots=True)
class PhaseErrors:
    phase: Phase
    moves: int
    avg_win_pct_loss: float
    inaccuracies: int
    mistakes: int
    blunders: int

    @property
    def serious_per_100(self) -> float:
        return 100 * (self.mistakes + self.blunders) / self.moves if self.moves else 0.0


@dataclass(frozen=True, slots=True)
class TimePressureErrors:
    """Mistakes + blunders on moves made under 10% of the clock vs. the rest."""

    low_moves: int
    low_serious: int
    normal_moves: int
    normal_serious: int

    @property
    def low_rate(self) -> float:
        return 100 * self.low_serious / self.low_moves if self.low_moves else 0.0

    @property
    def normal_rate(self) -> float:
        return 100 * self.normal_serious / self.normal_moves if self.normal_moves else 0.0


@dataclass(frozen=True, slots=True)
class Conversion:
    winning_games: int
    converted: int
    thrown: tuple[MomentRef, ...]

    @property
    def rate(self) -> float:
        return 100 * self.converted / self.winning_games if self.winning_games else 0.0


@dataclass(frozen=True, slots=True)
class EngineInsights:
    games: int
    accuracy: float | None
    opponent_accuracy: float | None
    by_phase: tuple[PhaseErrors, ...]
    time_pressure: TimePressureErrors | None
    missed_mates: tuple[MomentRef, ...]
    punish_opportunities: int
    unpunished: tuple[MomentRef, ...]
    conversion: Conversion


@dataclass(frozen=True, slots=True)
class TimeClassInsights:
    time_class: TimeClass
    overall: ResultSummary
    openings: tuple[OpeningRecord, ...]
    losses_by_termination: dict[str, int]
    wins_by_termination: dict[str, int]
    clock: ClockProfile | None
    streaks: StreakImpact
    by_session_position: tuple[LabelledSummary, ...]
    by_day_part: dict[DayPart, ResultSummary]
    by_weekday: tuple[LabelledSummary, ...]
    by_rating_gap: tuple[RatingGapBucket, ...]
    rating_by_month: tuple[MonthRating, ...]
    analyzed_games: int = 0
    engine: EngineInsights | None = None
