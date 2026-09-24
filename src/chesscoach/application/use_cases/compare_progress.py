from collections.abc import Callable, Sequence
from datetime import datetime, timedelta

from chesscoach.application.dto import PeriodMetrics, ProgressReport
from chesscoach.application.ports import AnalysisRepository, ClockReader, GameRepository
from chesscoach.domain.entities import Game
from chesscoach.domain.services.clock_usage import clock_profile
from chesscoach.domain.services.engine_insights import engine_insights
from chesscoach.domain.services.statistics import summarize
from chesscoach.domain.value_objects import TimeClass


class CompareProgress:
    def __init__(
        self,
        games: GameRepository,
        analyses: AnalysisRepository,
        clocks: ClockReader,
        clock: Callable[[], datetime],
    ) -> None:
        self._games = games
        self._analyses = analyses
        self._clocks = clocks
        self._clock = clock

    def execute(self, username: str, time_class: TimeClass, days: int) -> ProgressReport:
        games = [g for g in self._games.games_of(username) if g.time_class is time_class]
        now, period = self._clock(), timedelta(days=days)
        return ProgressReport(
            time_class=time_class,
            days=days,
            current=self._metrics(games, now - period, now),
            previous=self._metrics(games, now - 2 * period, now - period),
        )

    def _metrics(self, games: Sequence[Game], start: datetime, end: datetime) -> PeriodMetrics:
        period = [g for g in games if start < g.played_at <= end]
        before = [g for g in games if g.played_at <= start]
        summary = summarize(period)
        clock = clock_profile((g, self._clocks.clocks(g.pgn)) for g in period)
        analyses = self._analyses.get_many(g.id for g in period)
        engine = engine_insights([(g, analyses[g.id]) for g in period if g.id in analyses])
        serious = sum(p.mistakes + p.blunders for p in engine.by_phase) if engine else 0
        moves = sum(p.moves for p in engine.by_phase) if engine else 0
        return PeriodMetrics(
            games=summary.games,
            score_pct=summary.score_pct,
            rating_change=_rating_change(before, period),
            time_trouble_pct=100 * clock.in_trouble.games / clock.games if clock else None,
            losses_on_time_pct=(
                100 * clock.losses_on_time / clock.losses if clock and clock.losses else None
            ),
            analyzed_games=len(analyses),
            accuracy=engine.accuracy if engine else None,
            serious_per_100=100 * serious / moves if moves else None,
        )


def _rating_change(before: Sequence[Game], period: Sequence[Game]) -> int | None:
    if not period:
        return None
    start = before[-1].user.rating if before else period[0].user.rating
    return period[-1].user.rating - start
