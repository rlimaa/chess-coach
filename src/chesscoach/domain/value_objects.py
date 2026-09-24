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


class Phase(StrEnum):
    OPENING = "opening"
    MIDDLEGAME = "middlegame"
    ENDGAME = "endgame"


class MoveClass(StrEnum):
    BEST = "best"
    GOOD = "good"
    INACCURACY = "inaccuracy"
    MISTAKE = "mistake"
    BLUNDER = "blunder"


@dataclass(frozen=True, slots=True)
class Evaluation:
    """Engine score from White's point of view; mate_in > 0 means White mates."""

    centipawns: int | None = None
    mate_in: int | None = None

    def __post_init__(self) -> None:
        if (self.centipawns is None) == (self.mate_in is None):
            raise ValueError("An evaluation is either centipawns or mate, not both or neither")

    @classmethod
    def cp(cls, centipawns: int) -> "Evaluation":
        return cls(centipawns=centipawns)

    @classmethod
    def mate(cls, moves: int) -> "Evaluation":
        return cls(mate_in=moves)
