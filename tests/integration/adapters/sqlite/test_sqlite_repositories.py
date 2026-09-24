from pathlib import Path

from chesscoach.adapters.persistence.sqlite.database import SqliteDatabase
from chesscoach.adapters.persistence.sqlite.game_repository import SqliteGameRepository
from chesscoach.adapters.persistence.sqlite.response_cache import SqliteResponseCache
from chesscoach.adapters.persistence.sqlite.sync_state import SqliteSyncState
from chesscoach.application.dto import ArchiveMonth
from chesscoach.domain.entities import Accuracies, PlayerSide
from chesscoach.domain.value_objects import Color, Outcome, TimeClass, TimeControl
from tests.builders import make_game


def _db(tmp_path: Path) -> SqliteDatabase:
    return SqliteDatabase(tmp_path / "nested" / "coach.db")


def test_games_round_trip_with_every_field(tmp_path: Path) -> None:
    repo = SqliteGameRepository(_db(tmp_path))
    game = make_game(
        white=PlayerSide("rival", 1600),
        black=PlayerSide("Me", 1550),
        user_color=Color.BLACK,
        outcome=Outcome.DRAW,
        time_class=TimeClass.DAILY,
        time_control=TimeControl.parse("1/86400"),
        rated=False,
        eco=None,
        opening=None,
        accuracies=Accuracies(white=80.1, black=75.5),
    )

    repo.add([game])

    assert repo.games_of("me") == [game]


def test_adding_the_same_game_twice_stores_it_once(tmp_path: Path) -> None:
    repo = SqliteGameRepository(_db(tmp_path))

    assert repo.add([make_game(id="x")]) == 1
    assert repo.add([make_game(id="x"), make_game(id="y")]) == 1
    assert len(repo.games_of("me")) == 2


def test_games_are_returned_oldest_first_and_only_for_that_player(tmp_path: Path) -> None:
    repo = SqliteGameRepository(_db(tmp_path))
    newer = make_game(id="new", played_at=make_game().played_at.replace(day=5))
    older = make_game(id="old", played_at=make_game().played_at.replace(day=2))
    someone_else = make_game(id="other", white=PlayerSide("stranger", 1200))

    repo.add([newer, someone_else, older])

    assert [g.id for g in repo.games_of("me")] == ["old", "new"]


def test_data_persists_across_connections(tmp_path: Path) -> None:
    SqliteGameRepository(_db(tmp_path)).add([make_game(id="kept")])

    assert [g.id for g in SqliteGameRepository(_db(tmp_path)).games_of("me")] == ["kept"]


def test_sync_state_remembers_synced_months_per_player(tmp_path: Path) -> None:
    state = SqliteSyncState(_db(tmp_path))

    state.mark_synced("me", ArchiveMonth(2026, 8))
    state.mark_synced("me", ArchiveMonth(2026, 8))
    state.mark_synced("me", ArchiveMonth(2026, 9))

    assert state.synced_months("me") == {ArchiveMonth(2026, 8), ArchiveMonth(2026, 9)}
    assert state.synced_months("other") == set()


def test_response_cache_stores_latest_etag_and_body(tmp_path: Path) -> None:
    cache = SqliteResponseCache(_db(tmp_path))

    assert cache.get("https://x") is None
    cache.put("https://x", '"v1"', b"old")
    cache.put("https://x", '"v2"', b"new")

    cached = cache.get("https://x")
    assert cached is not None
    assert (cached.etag, cached.body) == ('"v2"', b"new")
