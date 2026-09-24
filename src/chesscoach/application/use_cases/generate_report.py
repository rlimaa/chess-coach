from collections.abc import Iterable
from zoneinfo import ZoneInfo

from chesscoach.application.dto import WrittenReport
from chesscoach.application.ports import (
    AnalysisRepository,
    ClockReader,
    GameRepository,
    ReportWriter,
)
from chesscoach.application.use_cases.build_insights import BuildInsights
from chesscoach.domain.value_objects import TimeClass


class GenerateReport:
    def __init__(
        self,
        games: GameRepository,
        analyses: AnalysisRepository,
        clocks: ClockReader,
        writer: ReportWriter,
        timezone: ZoneInfo,
    ) -> None:
        self._build = BuildInsights(games, analyses, clocks, timezone)
        self._writer = writer

    def execute(self, username: str, time_classes: Iterable[TimeClass]) -> list[WrittenReport]:
        reports = []
        for time_class in time_classes:
            bundle = self._build.execute(username, time_class)
            if bundle is None:
                continue
            location = self._writer.write(username, bundle.insights, bundle.highlights)
            reports.append(
                WrittenReport(
                    time_class, bundle.insights.overall.games, bundle.highlights, location
                )
            )
        return reports
