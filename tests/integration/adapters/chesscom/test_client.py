import httpx
import pytest
import respx

from chesscoach.adapters.chesscom.client import ChessComClient, InMemoryResponseCache
from chesscoach.application.dto import ArchiveMonth
from chesscoach.application.errors import GameSourceError, PlayerNotFoundError
from tests.fixtures.chesscom import load

BASE = "https://api.chess.com/pub/player/rodigola/games"
USER_AGENT = "chesscoach/0.1 (contact: me@example.com)"


def _client(cache: InMemoryResponseCache | None = None, max_retries: int = 3) -> ChessComClient:
    return ChessComClient(
        user_agent=USER_AGENT,
        cache=cache or InMemoryResponseCache(),
        max_retries=max_retries,
        sleep=lambda _seconds: None,
    )


@respx.mock
def test_lists_archive_months_oldest_first() -> None:
    respx.get(f"{BASE}/archives").respond(json=load("archives.json"))

    months = _client().archive_months("rodigola")

    assert months[0] == ArchiveMonth(2016, 3)
    assert months[-1] == ArchiveMonth(2026, 9)
    assert len(months) == len(load("archives.json")["archives"])


@respx.mock
def test_fetches_and_maps_games_of_a_month() -> None:
    respx.get(f"{BASE}/2026/09").respond(json=load("month.json"))

    games = _client().games_in_month("rodigola", ArchiveMonth(2026, 9))

    assert len(games) == 6
    assert all(g.user.username == "rodigola" for g in games)


@respx.mock
def test_sends_identifying_user_agent() -> None:
    route = respx.get(f"{BASE}/archives").respond(json=load("archives.json"))

    _client().archive_months("rodigola")

    assert route.calls.last.request.headers["User-Agent"] == USER_AGENT


@respx.mock
def test_retries_after_rate_limit() -> None:
    respx.get(f"{BASE}/archives").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "1"}),
            httpx.Response(200, json=load("archives.json")),
        ]
    )

    assert _client().archive_months("rodigola")[-1] == ArchiveMonth(2026, 9)


@respx.mock
def test_gives_up_after_max_retries() -> None:
    respx.get(f"{BASE}/archives").respond(429)

    with pytest.raises(GameSourceError):
        _client(max_retries=2).archive_months("rodigola")


@respx.mock
def test_unknown_player_raises_player_not_found() -> None:
    respx.get("https://api.chess.com/pub/player/ghost/games/archives").respond(404)

    with pytest.raises(PlayerNotFoundError):
        _client().archive_months("ghost")


@respx.mock
def test_reuses_cached_body_when_server_says_not_modified() -> None:
    route = respx.get(f"{BASE}/2026/09").mock(
        side_effect=[
            httpx.Response(200, json=load("month.json"), headers={"ETag": '"v1"'}),
            httpx.Response(304),
        ]
    )
    client = _client()
    client.games_in_month("rodigola", ArchiveMonth(2026, 9))

    games = client.games_in_month("rodigola", ArchiveMonth(2026, 9))

    assert route.calls.last.request.headers["If-None-Match"] == '"v1"'
    assert len(games) == 6
