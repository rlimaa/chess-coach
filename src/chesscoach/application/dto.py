from dataclasses import dataclass

from chesscoach.domain.services.statistics import ResultSummary
from chesscoach.domain.value_objects import Color, TimeClass


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
