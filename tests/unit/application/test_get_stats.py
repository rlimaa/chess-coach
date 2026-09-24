from datetime import UTC, datetime

from chesscoach.application.use_cases.get_stats import GetStats
from chesscoach.domain.entities import PlayerSide
from chesscoach.domain.value_objects import Color, Outcome, TimeClass
from tests.builders import make_game
from tests.fakes import InMemoryGameRepository


def _day(d: int) -> datetime:
    return datetime(2026, 9, d, tzinfo=UTC)


def _repo() -> InMemoryGameRepository:
    repo = InMemoryGameRepository()
    repo.add(
        [
            make_game(id="1", played_at=_day(1), white=PlayerSide("me", 1500), outcome=Outcome.WIN),
            make_game(
                id="2", played_at=_day(2), white=PlayerSide("me", 1520), outcome=Outcome.LOSS
            ),
            make_game(
                id="3",
                played_at=_day(3),
                white=PlayerSide("rival", 1500),
                black=PlayerSide("me", 1510),
                user_color=Color.BLACK,
                outcome=Outcome.DRAW,
                opening="Sicilian Defense",
            ),
            make_game(
                id="4",
                played_at=_day(4),
                time_class=TimeClass.RAPID,
                white=PlayerSide("me", 1300),
                outcome=Outcome.WIN,
            ),
        ]
    )
    return repo


def test_stats_summarize_results_overall_and_by_color() -> None:
    stats = GetStats(_repo()).execute("me")

    assert stats.overall.games == 4
    assert stats.by_color[Color.WHITE].wins == 2
    assert stats.by_color[Color.BLACK].draws == 1


def test_stats_per_time_class_show_current_and_peak_rating() -> None:
    blitz = GetStats(_repo()).execute("me").by_time_class[TimeClass.BLITZ]

    assert blitz.summary.games == 3
    assert blitz.current_rating == 1510
    assert blitz.peak_rating == 1520


def test_stats_rank_openings_by_number_of_games() -> None:
    openings = GetStats(_repo()).execute("me").openings

    assert [o.name for o in openings] == ["Italian Game", "Sicilian Defense"]
    assert openings[0].summary.games == 3


def test_stats_can_be_limited_to_one_time_class() -> None:
    stats = GetStats(_repo()).execute("me", time_class=TimeClass.RAPID)

    assert stats.overall.games == 1
    assert list(stats.by_time_class) == [TimeClass.RAPID]
