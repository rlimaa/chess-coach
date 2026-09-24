from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any

from chesscoach.adapters.reporting.markdown_report_writer import MarkdownReportWriter
from chesscoach.domain.insights import (
    ClockProfile,
    Conversion,
    DayPart,
    EngineInsights,
    Highlight,
    LabelledSummary,
    MomentRef,
    MonthRating,
    OpeningRecord,
    PhaseErrors,
    RatingGapBucket,
    TimePressureErrors,
)
from chesscoach.domain.value_objects import Color, Phase
from tests.builders import make_insights, summary

INSIGHTS = make_insights(
    openings=(
        OpeningRecord(Color.BLACK, "Caro Kann Defense", summary(wins=20, draws=2, losses=18)),
    ),
    losses_by_termination={"timeout": 30, "resigned": 20},
    wins_by_termination={"resigned": 40},
    clock=ClockProfile(
        games=100,
        in_trouble=summary(wins=10, losses=30),
        not_in_trouble=summary(wins=40, losses=20),
        losses=50,
        losses_on_time=30,
    ),
    by_session_position=(LabelledSummary("1st game", summary(wins=3, losses=1)),),
    by_day_part={DayPart.EVENING: summary(wins=5, losses=5)},
    by_weekday=(LabelledSummary("Monday", summary(wins=2)),),
    by_rating_gap=(RatingGapBucket("similar (±24)", summary(wins=6, losses=4), 50.0),),
    rating_by_month=(MonthRating(2026, 9, 1369, 147),),
)
HIGHLIGHTS = (
    Highlight(5.0, "60% of your losses are on time (30 of 50)."),
    Highlight(2.0, "As white, the Scotch Game is a strength.", strength=True),
)


def _write(tmp_path: Path) -> tuple[str, str]:
    writer = MarkdownReportWriter(tmp_path / "reports", today=lambda: date(2026, 9, 24))
    location = writer.write("rodigola", INSIGHTS, HIGHLIGHTS)
    return location, Path(location).read_text()


def test_report_is_written_to_a_dated_file_per_time_class(tmp_path: Path) -> None:
    location, _ = _write(tmp_path)

    assert location == str(tmp_path / "reports" / "2026-09-24-blitz.md")


def test_report_starts_with_highlights_split_into_weaknesses_and_strengths(
    tmp_path: Path,
) -> None:
    _, text = _write(tmp_path)

    assert text.startswith("# rodigola · blitz coaching report (2026-09-24)")
    weaknesses = text.index("## Work on")
    strengths = text.index("## Keep doing")
    assert weaknesses < text.index("60% of your losses are on time") < strengths
    assert text.index("Scotch Game is a strength") > strengths


def test_report_contains_every_insight_section_as_tables(tmp_path: Path) -> None:
    _, text = _write(tmp_path)

    for heading in (
        "## Openings",
        "## How games end",
        "## Clock",
        "## Habits",
        "## Opponents",
        "## Rating by month",
    ):
        assert heading in text
    assert "| black | Caro Kann Defense | 40 | 20/2/18 | 52.5% |" in text
    assert "| timeout | 30 |" in text
    assert "| 2026-09 | 1369 | 147 |" in text
    assert "| similar (±24) | 10 | 6/0/4 | 60.0% | 50.0% |" in text


ENGINE = EngineInsights(
    games=50,
    accuracy=81.25,
    opponent_accuracy=79.5,
    by_phase=(
        PhaseErrors(Phase.OPENING, 400, 1.5, 10, 4, 2),
        PhaseErrors(Phase.MIDDLEGAME, 800, 3.25, 30, 16, 8),
        PhaseErrors(Phase.ENDGAME, 0, 0.0, 0, 0, 0),
    ),
    time_pressure=TimePressureErrors(50, 15, 2000, 80),
    missed_mates=(MomentRef("https://www.chess.com/game/live/1", 40, "Qd1", "Qh2#"),),
    punish_opportunities=20,
    unpunished=(MomentRef("https://www.chess.com/game/live/2", 21, "a3", "Nxe5"),),
    conversion=Conversion(
        20, 15, (MomentRef("https://www.chess.com/game/live/3", 30, "Kh1", "Rd8"),)
    ),
)


def _write_insights(tmp_path: Path, **overrides: Any) -> str:
    writer = MarkdownReportWriter(tmp_path, today=lambda: date(2026, 9, 24))
    return Path(writer.write("rodigola", replace(INSIGHTS, **overrides), ())).read_text()


def test_engine_section_explains_when_the_sample_is_too_small(tmp_path: Path) -> None:
    text = _write_insights(tmp_path, analyzed_games=5, engine=None)

    assert "## Engine analysis" in text
    assert "5 games analyzed so far" in text


def test_engine_section_lists_errors_by_phase_and_key_moments(tmp_path: Path) -> None:
    text = _write_insights(tmp_path, analyzed_games=50, engine=ENGINE)

    assert "50 analyzed games · accuracy 81.2% (opponents 79.5%)" in text
    assert "| middlegame | 800 | 3.25 | 30 | 16 | 8 | 3.0 |" in text
    assert (
        "Under 10% of the clock: 30.0% of moves are mistakes or blunders (4.0% otherwise)." in text
    )
    assert "Converted 15 of 20 clearly winning positions (75.0%)." in text
    assert "Opponent blunders punished: 19 of 20." in text
    assert "[move 21](https://www.chess.com/game/live/1) Qd1, best Qh2#" in text
    assert "[move 11...](https://www.chess.com/game/live/2) a3, best Nxe5" in text
    assert "[move 16](https://www.chess.com/game/live/3) Kh1, best Rd8" in text
