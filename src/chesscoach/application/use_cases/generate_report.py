from collections.abc import Iterable, Sequence
from zoneinfo import ZoneInfo

from chesscoach.application.dto import WrittenReport
from chesscoach.application.ports import ClockReader, GameRepository, ReportWriter
from chesscoach.domain.entities import Game
from chesscoach.domain.insights import TimeClassInsights
from chesscoach.domain.services.clock_usage import clock_profile, termination_counts
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


class GenerateReport:
    def __init__(
        self,
        games: GameRepository,
        clocks: ClockReader,
        writer: ReportWriter,
        timezone: ZoneInfo,
    ) -> None:
        self._games = games
        self._clocks = clocks
        self._writer = writer
        self._timezone = timezone

    def execute(self, username: str, time_classes: Iterable[TimeClass]) -> list[WrittenReport]:
        all_games = self._games.games_of(username)
        reports = []
        for time_class in time_classes:
            games = [g for g in all_games if g.time_class is time_class]
            if not games:
                continue
            insights = self._insights(time_class, games)
            highlights = tuple(find_highlights(insights))
            location = self._writer.write(username, insights, highlights)
            reports.append(WrittenReport(time_class, len(games), highlights, location))
        return reports

    def _insights(self, time_class: TimeClass, games: Sequence[Game]) -> TimeClassInsights:
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
        )
