from chesscoach.application.dto import ArchiveMonth
from chesscoach.application.use_cases.sync_games import SyncGames
from tests.builders import make_game
from tests.fakes import FakeGameSource, InMemoryGameRepository, InMemorySyncState

AUG, SEP = ArchiveMonth(2026, 8), ArchiveMonth(2026, 9)


def _source() -> FakeGameSource:
    return FakeGameSource(
        {
            AUG: [make_game(id="a1"), make_game(id="a2")],
            SEP: [make_game(id="s1")],
        }
    )


def test_first_sync_stores_every_game() -> None:
    games = InMemoryGameRepository()
    sync = SyncGames(_source(), games, InMemorySyncState())

    report = sync.execute("me")

    assert report.games_added == 3
    assert {g.id for g in games.games_of("me")} == {"a1", "a2", "s1"}


def test_resync_only_refetches_the_latest_month_and_adds_nothing_new() -> None:
    source, games, state = _source(), InMemoryGameRepository(), InMemorySyncState()
    SyncGames(source, games, state).execute("me")
    source.fetched.clear()

    report = SyncGames(source, games, state).execute("me")

    assert source.fetched == [SEP]
    assert report.games_added == 0


def test_resync_picks_up_new_months_and_new_games_in_latest_month() -> None:
    source, games, state = _source(), InMemoryGameRepository(), InMemorySyncState()
    SyncGames(source, games, state).execute("me")
    oct_ = ArchiveMonth(2026, 10)
    source.archives[SEP].append(make_game(id="s2"))
    source.archives[oct_] = [make_game(id="o1")]
    source.fetched.clear()

    report = SyncGames(source, games, state).execute("me")

    assert source.fetched == [SEP, oct_]
    assert report.games_added == 2
