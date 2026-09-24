from chesscoach.domain.insights import (
    ClockProfile,
    LabelledSummary,
    MonthRating,
    OpeningRecord,
    RatingGapBucket,
    StreakImpact,
)
from chesscoach.domain.services.highlights import find_highlights
from chesscoach.domain.value_objects import Color
from tests.builders import make_insights, summary


def _texts(**overrides: object) -> list[str]:
    return [h.text for h in find_highlights(make_insights(**overrides))]


def test_an_even_profile_has_nothing_to_report() -> None:
    assert find_highlights(make_insights()) == []


def test_flags_a_frequently_played_opening_that_scores_well_below_average() -> None:
    weak = OpeningRecord(Color.BLACK, "Alapin Sicilian Defense", summary(wins=12, losses=28))
    rare = OpeningRecord(Color.WHITE, "Englund", summary(losses=5))

    texts = _texts(openings=(weak, rare))

    assert len(texts) == 1
    assert "Alapin Sicilian Defense" in texts[0]
    assert "black" in texts[0]
    assert "30%" in texts[0]


def test_reports_strong_openings_as_strengths() -> None:
    strong = OpeningRecord(Color.WHITE, "Scotch Game", summary(wins=30, losses=10))

    (highlight,) = find_highlights(make_insights(openings=(strong,)))

    assert highlight.strength
    assert "Scotch Game" in highlight.text


def test_flags_tilt_after_consecutive_losses() -> None:
    streaks = StreakImpact(
        fresh=summary(wins=55, losses=45),
        after_win=summary(wins=50, losses=50),
        after_loss=summary(wins=45, losses=55),
        after_two_plus_losses=summary(wins=12, losses=28),
    )

    (text,) = _texts(streaks=streaks)

    assert "two losses in a row" in text
    assert "30%" in text


def test_flags_time_trouble_and_losses_on_time() -> None:
    clock = ClockProfile(
        games=100,
        in_trouble=summary(wins=10, losses=30),
        not_in_trouble=summary(wins=40, losses=20),
        losses=50,
        losses_on_time=20,
    )

    texts = _texts(clock=clock)

    assert any("time trouble" in t and "40%" in t for t in texts)
    assert any("on time" in t and "40%" in t for t in texts)


def test_flags_long_sessions_and_underperformance_by_opponent_strength() -> None:
    sessions = (
        LabelledSummary("1st game", summary(wins=30, losses=20)),
        LabelledSummary("game 7+", summary(wins=12, losses=28)),
    )
    gaps = (RatingGapBucket("weaker (-25..-99)", summary(wins=20, losses=20), 64.0),)

    texts = _texts(by_session_position=sessions, by_rating_gap=gaps)

    assert any("game 7+" in t for t in texts)
    assert any("weaker (-25..-99)" in t and "64%" in t for t in texts)


def test_reports_rating_progress_over_the_last_three_months() -> None:
    months = tuple(
        MonthRating(2026, m, r, 20) for m, r in [(6, 1400), (7, 1420), (8, 1450), (9, 1480)]
    )

    (highlight,) = find_highlights(make_insights(rating_by_month=months))

    assert highlight.strength
    assert "+80" in highlight.text


def test_highlights_are_ordered_by_severity() -> None:
    weak = OpeningRecord(Color.BLACK, "Alapin Sicilian Defense", summary(wins=12, losses=28))
    very_weak = OpeningRecord(Color.WHITE, "Kings Gambit", summary(wins=5, losses=35))

    texts = _texts(openings=(weak, very_weak))

    assert "Kings Gambit" in texts[0]


def test_rating_trend_uses_calendar_months_even_with_gaps_in_play() -> None:
    months = tuple(
        MonthRating(y, m, r, 20) for y, m, r in [(2026, 1, 1300), (2026, 2, 1310), (2026, 8, 1400)]
    )

    (highlight,) = find_highlights(make_insights(rating_by_month=months))

    assert "+90" in highlight.text


def test_no_rating_trend_without_history_three_months_back() -> None:
    months = tuple(MonthRating(2026, m, 1400 + 10 * m, 20) for m in (7, 8, 9))

    assert find_highlights(make_insights(rating_by_month=months)) == []
