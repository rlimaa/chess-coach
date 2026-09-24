from dataclasses import dataclass
from enum import StrEnum

from chesscoach.domain.services.statistics import ResultSummary
from chesscoach.domain.value_objects import Color, TimeClass


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
