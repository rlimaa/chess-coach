from datetime import date
from pathlib import Path

from chesscoach.adapters.reporting.markdown_report_writer import MarkdownReportWriter
from chesscoach.domain.insights import (
    ClockProfile,
    DayPart,
    Highlight,
    LabelledSummary,
    MonthRating,
    OpeningRecord,
    RatingGapBucket,
)
from chesscoach.domain.value_objects import Color
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
