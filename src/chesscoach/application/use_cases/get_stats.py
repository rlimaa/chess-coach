from collections import defaultdict
from collections.abc import Sequence

from chesscoach.application.dto import OpeningStats, PlayerStats, TimeClassStats
from chesscoach.application.ports import GameRepository
from chesscoach.domain.entities import Game
from chesscoach.domain.services.statistics import summarize
from chesscoach.domain.value_objects import Color, TimeClass

UNKNOWN_OPENING = "Unknown"


class GetStats:
    def __init__(self, games: GameRepository) -> None:
        self._games = games

    def execute(
        self, username: str, time_class: TimeClass | None = None, top_openings: int = 10
    ) -> PlayerStats:
        games = [
            game
            for game in self._games.games_of(username)
            if time_class is None or game.time_class is time_class
        ]
        return PlayerStats(
            username=username,
            overall=summarize(games),
            by_color={
                color: summarize(g for g in games if g.user_color is color) for color in Color
            },
            by_time_class=_by_time_class(games),
            openings=_openings(games)[:top_openings],
        )


def _by_time_class(games: Sequence[Game]) -> dict[TimeClass, TimeClassStats]:
    grouped: dict[TimeClass, list[Game]] = defaultdict(list)
    for game in games:  # games are oldest first
        grouped[game.time_class].append(game)
    return {
        time_class: TimeClassStats(
            summary=summarize(group),
            current_rating=group[-1].user.rating,
            peak_rating=max(game.user.rating for game in group),
        )
        for time_class, group in grouped.items()
    }


def _openings(games: Sequence[Game]) -> list[OpeningStats]:
    grouped: dict[str, list[Game]] = defaultdict(list)
    for game in games:
        grouped[game.opening or UNKNOWN_OPENING].append(game)
    stats = [OpeningStats(name, summarize(group)) for name, group in grouped.items()]
    return sorted(stats, key=lambda s: s.summary.games, reverse=True)
