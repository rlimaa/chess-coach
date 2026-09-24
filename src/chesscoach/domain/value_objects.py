from dataclasses import dataclass
from enum import StrEnum


class Color(StrEnum):
    WHITE = "white"
    BLACK = "black"


class Outcome(StrEnum):
    """Result of a game from the point of view of the coached player."""

    WIN = "win"
    DRAW = "draw"
    LOSS = "loss"


class TimeClass(StrEnum):
    BULLET = "bullet"
    BLITZ = "blitz"
    RAPID = "rapid"
    DAILY = "daily"


@dataclass(frozen=True, slots=True)
class TimeControl:
    raw: str
    base_seconds: int
    increment_seconds: int
    is_correspondence: bool

    @classmethod
    def parse(cls, raw: str) -> "TimeControl":
        if "/" in raw:
            _, seconds_per_move = raw.split("/", 1)
            return cls(raw, int(seconds_per_move), 0, is_correspondence=True)
        base, _, increment = raw.partition("+")
        return cls(raw, int(base), int(increment or 0), is_correspondence=False)

    def __str__(self) -> str:
        return self.raw
