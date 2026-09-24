from collections.abc import Iterable
from dataclasses import dataclass

from chesscoach.domain.entities import Game
from chesscoach.domain.value_objects import Outcome


@dataclass(frozen=True, slots=True)
class ResultSummary:
    wins: int
    draws: int
    losses: int

    @property
    def games(self) -> int:
        return self.wins + self.draws + self.losses

    @property
    def score_pct(self) -> float:
        if self.games == 0:
            return 0.0
        return 100 * (self.wins + 0.5 * self.draws) / self.games


def summarize(games: Iterable[Game]) -> ResultSummary:
    outcomes = [game.outcome for game in games]
    return ResultSummary(
        wins=outcomes.count(Outcome.WIN),
        draws=outcomes.count(Outcome.DRAW),
        losses=outcomes.count(Outcome.LOSS),
    )
