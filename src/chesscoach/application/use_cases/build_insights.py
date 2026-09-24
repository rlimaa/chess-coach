from collections.abc import Sequence
from zoneinfo import ZoneInfo

from chesscoach.application.dto import InsightsBundle
from chesscoach.application.ports import AnalysisRepository, ClockReader, GameRepository
from chesscoach.domain.entities import Game, GameAnalysis
from chesscoach.domain.insights import EngineInsights, TimeClassInsights
from chesscoach.domain.services.clock_usage import clock_profile, termination_counts
from chesscoach.domain.services.engine_insights import engine_insights
from chesscoach.domain.services.habits import (
    by_day_part,
    by_session_position,
    by_weekday,
    streak_impact,
)
from chesscoach.domain.services.highlights import find_highlights
from chesscoach.domain.services.openings import opening_records
from chesscoach.domain.services.opponents import by_rating_gap
from chesscoach.domain.services.rating_trend import rating_by_month
from chesscoach.domain.services.statistics import summarize
from chesscoach.domain.value_objects import Outcome, TimeClass

MIN_OPENING_GAMES = 10
MIN_ANALYZED_GAMES = 20


class BuildInsights:
    def __init__(
        self,
        games: GameRepository,
        analyses: AnalysisRepository,
        clocks: ClockReader,
        timezone: ZoneInfo,
    ) -> None:
        self._games = games
        self._analyses = analyses
        self._clocks = clocks
        self._timezone = timezone

    def execute(self, username: str, time_class: TimeClass) -> InsightsBundle | None:
        games = [g for g in self._games.games_of(username) if g.time_class is time_class]
        if not games:
            return None
        insights = self._insights(time_class, games)
        return InsightsBundle(insights, tuple(find_highlights(insights)))

    def _insights(self, time_class: TimeClass, games: Sequence[Game]) -> TimeClassInsights:
        analyses = self._analyses.get_many(g.id for g in games)
        return TimeClassInsights(
            time_class=time_class,
            overall=summarize(games),
            openings=tuple(opening_records(games, min_games=MIN_OPENING_GAMES)),
            losses_by_termination=termination_counts(games, Outcome.LOSS),
            wins_by_termination=termination_counts(games, Outcome.WIN),
            clock=clock_profile((g, self._clocks.clocks(g.pgn)) for g in games),
            streaks=streak_impact(games),
            by_session_position=tuple(by_session_position(games)),
            by_day_part=by_day_part(games, self._timezone),
            by_weekday=tuple(by_weekday(games, self._timezone)),
            by_rating_gap=tuple(by_rating_gap(games)),
            rating_by_month=tuple(rating_by_month(games)),
            analyzed_games=len(analyses),
            engine=self._engine_insights(games, analyses),
        )

    @staticmethod
    def _engine_insights(
        games: Sequence[Game], analyses: dict[str, GameAnalysis]
    ) -> EngineInsights | None:
        if len(analyses) < MIN_ANALYZED_GAMES:
            return None
        return engine_insights([(g, analyses[g.id]) for g in games if g.id in analyses])
