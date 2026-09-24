from dataclasses import dataclass
from datetime import datetime

from chesscoach.domain.value_objects import Color, MoveClass, Phase, TimeClass


@dataclass(frozen=True, slots=True)
class Puzzle:
    """A position from the user's own game where they went wrong; the engine move solves it."""

    id: str
    game_id: str
    game_url: str
    played_at: datetime
    time_class: TimeClass
    opponent: str
    ply: int
    color: Color
    fen: str
    played_san: str
    solution_san: str
    mistake: MoveClass
    phase: Phase
    win_pct_loss: float


@dataclass(frozen=True, slots=True)
class Attempt:
    puzzle_id: str
    attempted_at: datetime
    solved: bool
