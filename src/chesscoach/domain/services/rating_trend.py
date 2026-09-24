from collections.abc import Iterable
from itertools import groupby

from chesscoach.domain.entities import Game
from chesscoach.domain.insights import MonthRating


def rating_by_month(games: Iterable[Game]) -> list[MonthRating]:
    chronological = sorted(games, key=lambda g: g.played_at)
    months = []
    for (year, month), group in groupby(
        chronological, key=lambda g: (g.played_at.year, g.played_at.month)
    ):
        month_games = list(group)
        months.append(MonthRating(year, month, month_games[-1].user.rating, len(month_games)))
    return months
