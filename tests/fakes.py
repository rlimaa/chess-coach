"""In-memory fakes for application ports. Only port boundaries are faked."""

from collections.abc import Iterable, Sequence

from chesscoach.application.dto import ArchiveMonth, EngineLine, ReplayedGame
from chesscoach.domain.entities import Game, GameAnalysis
from chesscoach.domain.insights import Highlight, TimeClassInsights
from chesscoach.domain.puzzles import Attempt
from chesscoach.domain.value_objects import Color


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

    def find(self, reference: str) -> Game | None:
        return next(
            (
                g
                for g in self._games.values()
                if reference in (g.id, g.url) or g.url.endswith(f"/{reference}")
            ),
            None,
        )


class InMemorySyncState:
    def __init__(self) -> None:
        self._months: dict[str, set[ArchiveMonth]] = {}

    def synced_months(self, username: str) -> set[ArchiveMonth]:
        return set(self._months.get(username, set()))

    def mark_synced(self, username: str, month: ArchiveMonth) -> None:
        self._months.setdefault(username, set()).add(month)


class FakeReplayer:
    def __init__(self, games: dict[str, ReplayedGame]) -> None:
        self._games = games

    def replay(self, pgn: str) -> ReplayedGame:
        return self._games[pgn]


class FakeEngine:
    def __init__(self, lines: dict[str, EngineLine]) -> None:
        self._lines = lines
        self.calls: list[tuple[str, int]] = []

    def evaluate(self, fen: str, depth: int) -> EngineLine:
        self.calls.append((fen, depth))
        return self._lines[fen]


class InMemoryAnalysisRepository:
    def __init__(self) -> None:
        self._analyses: dict[str, GameAnalysis] = {}

    def save(self, analysis: GameAnalysis) -> None:
        self._analyses[analysis.game_id] = analysis

    def get(self, game_id: str) -> GameAnalysis | None:
        return self._analyses.get(game_id)

    def analyzed_ids(self) -> set[str]:
        return set(self._analyses)

    def get_many(self, game_ids: Iterable[str]) -> dict[str, GameAnalysis]:
        return {gid: self._analyses[gid] for gid in game_ids if gid in self._analyses}


class FakeClockReader:
    def __init__(self, clocks: dict[str, list[float]]) -> None:
        self._clocks = clocks

    def clocks(self, pgn: str) -> Sequence[float]:
        return self._clocks.get(pgn, [])


class InMemoryReportWriter:
    def __init__(self) -> None:
        self.written: list[tuple[str, TimeClassInsights, Sequence[Highlight]]] = []

    def write(
        self, username: str, insights: TimeClassInsights, highlights: Sequence[Highlight]
    ) -> str:
        self.written.append((username, insights, highlights))
        return f"memory://{insights.time_class.value}"


class FakeChessRules:
    def __init__(self, legal: dict[str, str]) -> None:
        self._legal = legal

    def normalize_move(self, fen: str, text: str) -> str | None:
        return self._legal.get(text.strip())

    def render(self, fen: str, perspective: Color) -> str:
        return f"board {fen} as {perspective.value}"


class InMemoryPuzzleAttempts:
    def __init__(self) -> None:
        self._attempts: list[Attempt] = []

    def record(self, attempt: Attempt) -> None:
        self._attempts.append(attempt)

    def all(self) -> list[Attempt]:
        return sorted(self._attempts, key=lambda a: a.attempted_at)
