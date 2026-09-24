from collections import defaultdict
from collections.abc import Iterable

from chesscoach.domain.entities import Game
from chesscoach.domain.insights import OpeningRecord
from chesscoach.domain.services.statistics import summarize
from chesscoach.domain.value_objects import Color

UNKNOWN = "Unknown"
_FAMILY_WORDS = frozenset({"Defense", "Game", "Opening", "Gambit", "Attack", "System"})


def opening_family(name: str | None) -> str:
    if not name:
        return UNKNOWN
    words = name.split()
    end = next((i for i, word in enumerate(words, start=1) if word in _FAMILY_WORDS), len(words))
    return " ".join(words[:end])


def opening_records(games: Iterable[Game], min_games: int) -> list[OpeningRecord]:
    groups: dict[tuple[Color, str], list[Game]] = defaultdict(list)
    for game in games:
        groups[game.user_color, opening_family(game.opening)].append(game)
    records = [
        OpeningRecord(color, family, summarize(group))
        for (color, family), group in groups.items()
        if len(group) >= min_games
    ]
    return sorted(records, key=lambda r: r.summary.games, reverse=True)
