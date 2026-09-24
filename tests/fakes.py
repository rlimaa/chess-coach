"""In-memory fakes for application ports. Only port boundaries are faked."""

from collections.abc import Iterable, Sequence

from chesscoach.application.dto import ArchiveMonth
from chesscoach.domain.entities import Game


class FakeGameSource:
    def __init__(self, archives: dict[ArchiveMonth, list[Game]]) -> None:
        self.archives = archives
        self.fetched: list[ArchiveMonth] = []

    def archive_months(self, username: str) -> Sequence[ArchiveMonth]:
        return sorted(self.archives)

    def games_in_month(self, username: str, month: ArchiveMonth) -> Sequence[Game]:
        self.fetched.append(month)
        return self.archives[month]


class InMemoryGameRepository:
    def __init__(self) -> None:
        self._games: dict[str, Game] = {}

    def add(self, games: Iterable[Game]) -> int:
        added = 0
        for game in games:
            if game.id not in self._games:
                self._games[game.id] = game
                added += 1
        return added

    def games_of(self, username: str) -> Sequence[Game]:
        mine = [g for g in self._games.values() if g.user.username.lower() == username.lower()]
        return sorted(mine, key=lambda g: g.played_at)


class InMemorySyncState:
    def __init__(self) -> None:
        self._months: dict[str, set[ArchiveMonth]] = {}

    def synced_months(self, username: str) -> set[ArchiveMonth]:
        return set(self._months.get(username, set()))

    def mark_synced(self, username: str, month: ArchiveMonth) -> None:
        self._months.setdefault(username, set()).add(month)
