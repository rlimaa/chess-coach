from dataclasses import dataclass
from datetime import datetime

from chesscoach.domain.services.classification import game_accuracy, move_accuracy
from chesscoach.domain.value_objects import (
    Color,
    Evaluation,
    MoveClass,
    Outcome,
    Phase,
    TimeClass,
    TimeControl,
)


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
    def opponent_color(self) -> Color:
        return Color.BLACK if self.user_color is Color.WHITE else Color.WHITE

    @property
    def user_accuracy(self) -> float | None:
        if self.accuracies is None:
            return None
        return self.accuracies.white if self.user_color is Color.WHITE else self.accuracies.black


@dataclass(frozen=True, slots=True)
class MoveAnalysis:
    ply: int
    color: Color
    san: str
    fen_before: str
    phase: Phase
    eval_before: Evaluation
    eval_after: Evaluation
    best_move_san: str | None
    win_pct_loss: float
    move_class: MoveClass
    clock_seconds: float | None


@dataclass(frozen=True, slots=True)
class GameAnalysis:
    game_id: str
    depth: int
    moves: tuple[MoveAnalysis, ...]

    def accuracy(self, color: Color) -> float | None:
        return game_accuracy(
            [move_accuracy(m.win_pct_loss) for m in self.moves if m.color is color]
        )

    def count(self, color: Color, move_class: MoveClass) -> int:
        return sum(m.color is color and m.move_class is move_class for m in self.moves)
