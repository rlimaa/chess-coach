from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from chesscoach.domain.entities import Game
from chesscoach.domain.insights import DayPart
from chesscoach.domain.services.habits import (
    by_day_part,
    by_session_position,
    by_weekday,
    streak_impact,
)
from chesscoach.domain.value_objects import Outcome
from tests.builders import make_game

T0 = datetime(2026, 9, 7, 9, 0, tzinfo=UTC)  # a Monday


def _session(start: datetime, *outcomes: Outcome, gap_minutes: int = 10) -> list[Game]:
    return [
        make_game(
            id=f"{start:%d%H}-{i}", played_at=start + timedelta(minutes=gap_minutes * i), outcome=o
        )
        for i, o in enumerate(outcomes)
    ]


def test_streak_impact_looks_at_the_previous_game_of_the_same_sitting() -> None:
    games = _session(T0, Outcome.LOSS, Outcome.LOSS, Outcome.LOSS, Outcome.WIN, Outcome.DRAW)
    games += _session(T0 + timedelta(days=1), Outcome.WIN)

    impact = streak_impact(games)

    assert impact.fresh.games == 2
    assert (impact.after_loss.games, impact.after_loss.losses) == (3, 2)
    assert (impact.after_two_plus_losses.games, impact.after_two_plus_losses.wins) == (2, 1)
    assert (impact.after_win.games, impact.after_win.draws) == (1, 1)


def test_games_more_than_an_hour_apart_start_a_new_sitting() -> None:
    games = _session(T0, Outcome.LOSS, Outcome.WIN, gap_minutes=61)

    assert streak_impact(games).fresh.games == 2


def test_session_position_buckets() -> None:
    games = _session(T0, *[Outcome.WIN] * 3, *[Outcome.LOSS] * 5)

    buckets = {b.label: b.summary for b in by_session_position(games)}

    assert list(buckets) == ["1st game", "games 2-3", "games 4-6", "game 7+"]
    assert buckets["1st game"].wins == 1
    assert (buckets["games 2-3"].wins, buckets["games 4-6"].losses) == (2, 3)
    assert buckets["game 7+"].games == 2


def test_day_parts_and_weekdays_use_the_players_timezone() -> None:
    late_evening_utc = datetime(2026, 9, 7, 23, 30, tzinfo=UTC)  # Tue 01:30 in Madrid
    games = [make_game(played_at=late_evening_utc)]
    madrid = ZoneInfo("Europe/Madrid")

    assert by_day_part(games, madrid)[DayPart.NIGHT].games == 1
    weekdays = {b.label: b.summary.games for b in by_weekday(games, madrid)}
    assert weekdays["Tuesday"] == 1
    assert next(iter(weekdays)) == "Monday"
