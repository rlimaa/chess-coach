from chesscoach.application.dto import ArchiveMonth, SyncReport
from chesscoach.application.ports import GameRepository, GameSource, SyncStateRepository


class SyncGames:
    def __init__(
        self, source: GameSource, games: GameRepository, sync_state: SyncStateRepository
    ) -> None:
        self._source = source
        self._games = games
        self._sync_state = sync_state

    def execute(self, username: str) -> SyncReport:
        fetched = added = 0
        months = self._months_to_fetch(username)
        for month in months:
            games = self._source.games_in_month(username, month)
            fetched += len(games)
            added += self._games.add(games)
            self._sync_state.mark_synced(username, month)
        return SyncReport(months_fetched=len(months), games_fetched=fetched, games_added=added)

    def _months_to_fetch(self, username: str) -> list[ArchiveMonth]:
        """Unsynced months, plus the last synced one since it may have been incomplete."""
        available = self._source.archive_months(username)
        synced = self._sync_state.synced_months(username)
        pending = {month for month in available if month not in synced}
        if synced:
            pending.add(max(synced))
        return sorted(pending)
