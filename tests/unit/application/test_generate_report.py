from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from chesscoach.application.use_cases.generate_report import GenerateReport
from chesscoach.domain.value_objects import Color, Outcome, TimeClass, TimeControl
from tests.builders import make_analysis, make_game, make_move
from tests.fakes import (
    FakeClockReader,
    InMemoryAnalysisRepository,
    InMemoryGameRepository,
    InMemoryReportWriter,
)


def _games() -> InMemoryGameRepository:
    repo = InMemoryGameRepository()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    repo.add(
        make_game(
            id=f"b{i}",
            pgn=f"b{i}",
            played_at=start + timedelta(days=i),
            time_class=TimeClass.BLITZ,
            time_control=TimeControl.parse("300"),
            user_color=Color.WHITE,
            opening="Kings Gambit Accepted",
            outcome=Outcome.LOSS if i % 4 else Outcome.WIN,
            termination="timeout" if i % 4 else "resigned",
        )
        for i in range(40)
    )
    repo.add(make_game(id=f"r{i}", time_class=TimeClass.RAPID) for i in range(3))
    return repo


def _use_case(
    writer: InMemoryReportWriter, analyses: InMemoryAnalysisRepository | None = None
) -> GenerateReport:
    clocks = FakeClockReader({f"b{i}": [290.0, 280.0, 20.0, 270.0] for i in range(40)})
    return GenerateReport(
        _games(), analyses or InMemoryAnalysisRepository(), clocks, writer, ZoneInfo("UTC")
    )


def _analyzed(count: int) -> InMemoryAnalysisRepository:
    analyses = InMemoryAnalysisRepository()
    for i in range(count):
        analyses.save(make_analysis(make_game(id=f"b{i}"), make_move(color=Color.WHITE)))
    return analyses


def test_writes_one_report_per_requested_time_class() -> None:
    writer = InMemoryReportWriter()

    reports = _use_case(writer).execute("me", [TimeClass.BLITZ, TimeClass.RAPID])

    assert [(r.time_class, r.games) for r in reports] == [
        (TimeClass.BLITZ, 40),
        (TimeClass.RAPID, 3),
    ]
    assert reports[0].location == "memory://blitz"
    assert [insights.time_class for _, insights, _ in writer.written] == [
        TimeClass.BLITZ,
        TimeClass.RAPID,
    ]


def test_blitz_report_combines_openings_clock_and_highlights() -> None:
    writer = InMemoryReportWriter()

    blitz = _use_case(writer).execute("me", [TimeClass.BLITZ])[0]

    _, insights, _ = writer.written[0]
    assert insights.openings[0].family == "Kings Gambit"
    assert insights.clock is not None
    assert insights.clock.in_trouble.games == 40
    assert insights.losses_by_termination == {"timeout": 30}
    assert any("on time" in h.text for h in blitz.highlights)


def test_time_classes_without_games_are_skipped() -> None:
    writer = InMemoryReportWriter()

    assert _use_case(writer).execute("me", [TimeClass.BULLET]) == []
    assert writer.written == []


def test_engine_insights_need_a_minimum_sample_of_analyzed_games() -> None:
    writer = InMemoryReportWriter()

    _use_case(writer, _analyzed(19)).execute("me", [TimeClass.BLITZ])

    _, insights, _ = writer.written[0]
    assert insights.analyzed_games == 19
    assert insights.engine is None


def test_engine_insights_are_included_once_enough_games_are_analyzed() -> None:
    writer = InMemoryReportWriter()

    _use_case(writer, _analyzed(20)).execute("me", [TimeClass.BLITZ])

    _, insights, _ = writer.written[0]
    assert insights.analyzed_games == 20
    assert insights.engine is not None
    assert insights.engine.games == 20
