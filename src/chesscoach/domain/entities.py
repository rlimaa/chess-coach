from dataclasses import dataclass
from datetime import datetime

from chesscoach.domain.value_objects import Color, Outcome, TimeClass, TimeControl


@dataclass(frozen=True, slots=True)
class PlayerSide:
    username: str
    rating: int


@dataclass(frozen=True, slots=True)
class Accuracies:
    white: float
    black: float


@dataclass(frozen=True, slots=True)
class Game:
    """A finished game, always seen from the coached player's perspective."""

    id: str
    url: str
    played_at: datetime
    time_class: TimeClass
    time_control: TimeControl
    rated: bool
    white: PlayerSide
    black: PlayerSide
    user_color: Color
    outcome: Outcome
    termination: str
    eco: str | None
    opening: str | None
    pgn: str
    accuracies: Accuracies | None

    @property
    def user(self) -> PlayerSide:
        return self.white if self.user_color is Color.WHITE else self.black

    @property
    def opponent(self) -> PlayerSide:
        return self.black if self.user_color is Color.WHITE else self.white

    @property
    def user_accuracy(self) -> float | None:
        if self.accuracies is None:
            return None
        return self.accuracies.white if self.user_color is Color.WHITE else self.accuracies.black
