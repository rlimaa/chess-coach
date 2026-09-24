from collections.abc import Iterable, Sequence
from typing import Protocol

from chesscoach.application.dto import ArchiveMonth
from chesscoach.domain.entities import Game


class GameSource(Protocol):
    def archive_months(self, username: str) -> Sequence[ArchiveMonth]: ...

    def games_in_month(self, username: str, month: ArchiveMonth) -> Sequence[Game]: ...


class GameRepository(Protocol):
    def add(self, games: Iterable[Game]) -> int:
        """Store games, ignoring ones already stored. Returns how many were new."""
        ...

    def games_of(self, username: str) -> Sequence[Game]:
        """All stored games of a player, oldest first."""
        ...


class SyncStateRepository(Protocol):
    def synced_months(self, username: str) -> set[ArchiveMonth]: ...

    def mark_synced(self, username: str, month: ArchiveMonth) -> None: ...
