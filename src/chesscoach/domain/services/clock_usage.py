from collections import Counter
from collections.abc import Iterable, Sequence

from chesscoach.domain.entities import Game
from chesscoach.domain.insights import ClockProfile
from chesscoach.domain.services.statistics import summarize
from chesscoach.domain.value_objects import Color, Outcome

TIME_TROUBLE_SHARE = 0.10
TIMEOUT = "timeout"


def clock_profile(games_with_clocks: Iterable[tuple[Game, Sequence[float]]]) -> ClockProfile | None:
    in_trouble: list[Game] = []
    calm: list[Game] = []
    for game, clocks in games_with_clocks:
        own_clocks = clocks[0::2] if game.user_color is Color.WHITE else clocks[1::2]
        if game.time_control.is_correspondence or not own_clocks:
            continue
        limit = TIME_TROUBLE_SHARE * game.time_control.base_seconds
        (in_trouble if min(own_clocks) < limit else calm).append(game)

    counted = in_trouble + calm
    if not counted:
        return None
    losses = [g for g in counted if g.outcome is Outcome.LOSS]
    return ClockProfile(
        games=len(counted),
        in_trouble=summarize(in_trouble),
        not_in_trouble=summarize(calm),
        losses=len(losses),
        losses_on_time=sum(g.termination == TIMEOUT for g in losses),
    )


def termination_counts(games: Iterable[Game], outcome: Outcome) -> dict[str, int]:
    return dict(Counter(g.termination for g in games if g.outcome is outcome).most_common())
