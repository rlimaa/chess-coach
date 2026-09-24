from collections import defaultdict
from collections.abc import Iterable

from chesscoach.domain.entities import Game
from chesscoach.domain.insights import OpeningRecord
from chesscoach.domain.services.statistics import summarize
from chesscoach.domain.value_objects import Color

UNKNOWN = "Unknown"
_UNNAMED = frozenset({"", "Undefined"})
_FAMILY_WORDS = frozenset({"Defense", "Game", "Opening", "Gambit", "Attack", "System"})


def opening_family(name: str | None) -> str:
    if name is None or name in _UNNAMED:
        return UNKNOWN
    words = name.split()
    end = next((i for i, word in enumerate(words, start=1) if word in _FAMILY_WORDS), len(words))
    return " ".join(words[:end])


def _canonical(families: set[str]) -> dict[str, str]:
    """chess.com sometimes shortens a name ('Scotch'); map it to the full family ('Scotch Game')."""
    return {
        family: min((f for f in families if f.startswith(f"{family} ")), key=len, default=family)
        for family in families
    }


def opening_records(games: Iterable[Game], min_games: int) -> list[OpeningRecord]:
    with_family = [(game, opening_family(game.opening)) for game in games]
    canonical = _canonical({family for _, family in with_family})
    groups: dict[tuple[Color, str], list[Game]] = defaultdict(list)
    for game, family in with_family:
        groups[game.user_color, canonical[family]].append(game)
    records = [
        OpeningRecord(color, family, summarize(group))
        for (color, family), group in groups.items()
        if len(group) >= min_games
    ]
    return sorted(records, key=lambda r: r.summary.games, reverse=True)
