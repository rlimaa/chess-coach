from datetime import UTC, datetime

import pytest

from chesscoach.domain.entities import Game, PlayerSide
from chesscoach.domain.services.opponents import by_rating_gap
from chesscoach.domain.services.rating_trend import rating_by_month
from chesscoach.domain.value_objects import Outcome
from tests.builders import make_game


def _vs(opponent_rating: int, outcome: Outcome) -> Game:
    return make_game(
        white=PlayerSide("me", 1500), black=PlayerSide("rival", opponent_rating), outcome=outcome
    )


def test_rating_gap_buckets_compare_score_with_elo_expectation() -> None:
    games = [_vs(1700, Outcome.LOSS), _vs(1650, Outcome.WIN), _vs(1500, Outcome.DRAW)]

    buckets = {b.label: b for b in by_rating_gap(games)}

    assert list(buckets) == [
        "much stronger (+100)",
        "stronger (+25..+99)",
        "similar (±24)",
        "weaker (-25..-99)",
        "much weaker (-100)",
    ]
    much_stronger = buckets["much stronger (+100)"]
    assert much_stronger.summary.games == 2
    assert much_stronger.summary.score_pct == 50.0
    assert much_stronger.expected_score_pct == pytest.approx((24.03 + 29.66) / 2, abs=0.1)
    assert buckets["similar (±24)"].expected_score_pct == 50.0
    assert buckets["weaker (-25..-99)"].expected_score_pct == 0.0


def test_rating_by_month_takes_the_last_rating_of_each_month() -> None:
    games = [
        make_game(white=PlayerSide("me", r), played_at=datetime(2026, m, d, tzinfo=UTC))
        for m, d, r in [(8, 1, 1400), (8, 30, 1420), (9, 2, 1410)]
    ]

    months = rating_by_month(games)

    assert [(m.year, m.month, m.rating, m.games) for m in months] == [
        (2026, 8, 1420, 2),
        (2026, 9, 1410, 1),
    ]


def test_rating_gap_is_estimated_before_the_game_not_from_post_game_ratings() -> None:
    # Both players were 1500 before game 2; chess.com reports ratings after it (1516 vs 1484).
    first = make_game(
        id="1",
        played_at=datetime(2026, 9, 1, tzinfo=UTC),
        white=PlayerSide("me", 1500),
        black=PlayerSide("x", 1500),
    )
    won = make_game(
        id="2",
        played_at=datetime(2026, 9, 2, tzinfo=UTC),
        white=PlayerSide("me", 1516),
        black=PlayerSide("y", 1484),
        outcome=Outcome.WIN,
    )

    buckets = {b.label: b.summary.games for b in by_rating_gap([won, first])}

    assert buckets["similar (±24)"] == 2
