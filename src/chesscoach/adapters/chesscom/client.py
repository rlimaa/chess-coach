import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from chesscoach.adapters.chesscom.mapper import to_game
from chesscoach.application.dto import ArchiveMonth
from chesscoach.application.errors import GameSourceError, PlayerNotFoundError
from chesscoach.domain.entities import Game

DEFAULT_BASE_URL = "https://api.chess.com/pub"


class CachedResponse(Protocol):
    @property
    def etag(self) -> str: ...

    @property
    def body(self) -> bytes: ...


@dataclass(frozen=True, slots=True)
class _Entry:
    etag: str
    body: bytes


class ResponseCache(Protocol):
    def get(self, url: str) -> CachedResponse | None: ...

    def put(self, url: str, etag: str, body: bytes) -> None: ...


class InMemoryResponseCache:
    def __init__(self) -> None:
        self._entries: dict[str, CachedResponse] = {}

    def get(self, url: str) -> CachedResponse | None:
        return self._entries.get(url)

    def put(self, url: str, etag: str, body: bytes) -> None:
        self._entries[url] = _Entry(etag, body)


class ChessComClient:
    def __init__(
        self,
        *,
        user_agent: str,
        cache: ResponseCache,
        max_retries: int = 3,
        sleep: Callable[[float], None] = time.sleep,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        self._http = httpx.Client(headers={"User-Agent": user_agent}, timeout=30.0)
        self._cache = cache
        self._max_retries = max_retries
        self._sleep = sleep
        self._base_url = base_url

    def archive_months(self, username: str) -> list[ArchiveMonth]:
        data = self._get_json(f"{self._games_url(username)}/archives")
        return sorted(_archive_month(url) for url in data["archives"])

    def games_in_month(self, username: str, month: ArchiveMonth) -> list[Game]:
        data = self._get_json(f"{self._games_url(username)}/{month.year}/{month.month:02d}")
        return [game for raw in data["games"] if (game := to_game(raw, username)) is not None]

    def _games_url(self, username: str) -> str:
        return f"{self._base_url}/player/{username.lower()}/games"

    def _get_json(self, url: str) -> dict[str, Any]:
        cached = self._cache.get(url)
        headers = {"If-None-Match": cached.etag} if cached else {}
        for attempt in range(self._max_retries + 1):
            try:
                response = self._http.get(url, headers=headers)
            except httpx.HTTPError as error:
                raise GameSourceError(f"Request to {url} failed: {error}") from error

            if response.status_code == httpx.codes.TOO_MANY_REQUESTS:
                if attempt < self._max_retries:
                    self._sleep(float(response.headers.get("Retry-After", 2**attempt)))
                continue
            if response.status_code == httpx.codes.NOT_FOUND:
                raise PlayerNotFoundError(url)
            if response.status_code == httpx.codes.NOT_MODIFIED and cached:
                return _decode(cached.body)
            if not response.is_success:
                raise GameSourceError(f"{url} answered HTTP {response.status_code}")

            if etag := response.headers.get("ETag"):
                self._cache.put(url, etag, response.content)
            return _decode(response.content)
        raise GameSourceError(f"Still rate limited after {self._max_retries} retries: {url}")


def _archive_month(archive_url: str) -> ArchiveMonth:
    year, month = archive_url.rstrip("/").split("/")[-2:]
    return ArchiveMonth(int(year), int(month))


def _decode(body: bytes) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(body)
    return data
