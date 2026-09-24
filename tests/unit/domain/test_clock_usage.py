from chesscoach.domain.services.clock_usage import clock_profile, termination_counts
from chesscoach.domain.value_objects import Color, Outcome, TimeClass, TimeControl
from tests.builders import make_game

BLITZ = TimeControl.parse("300")


def test_time_trouble_is_the_user_dropping_below_ten_percent_of_base_time() -> None:
    calm = make_game(time_control=BLITZ, user_color=Color.WHITE, outcome=Outcome.WIN)
    panicked = make_game(
        time_control=BLITZ, user_color=Color.BLACK, outcome=Outcome.LOSS, termination="timeout"
    )
    profile = clock_profile(
        [
            (calm, [290.0, 280.0, 200.0, 150.0]),
            (panicked, [290.0, 280.0, 250.0, 25.0]),
        ]
    )

    assert profile is not None
    assert profile.games == 2
    assert (profile.in_trouble.games, profile.in_trouble.losses) == (1, 1)
    assert profile.not_in_trouble.wins == 1
    assert (profile.losses, profile.losses_on_time) == (1, 1)


def test_games_without_clocks_or_correspondence_games_are_ignored() -> None:
    daily = make_game(time_class=TimeClass.DAILY, time_control=TimeControl.parse("1/86400"))

    assert clock_profile([(make_game(), []), (daily, [80000.0, 70000.0])]) is None


def test_termination_counts_per_outcome() -> None:
    games = [
        make_game(outcome=Outcome.LOSS, termination="timeout"),
        make_game(outcome=Outcome.LOSS, termination="timeout"),
        make_game(outcome=Outcome.LOSS, termination="resigned"),
        make_game(outcome=Outcome.WIN, termination="checkmated"),
    ]

    assert termination_counts(games, Outcome.LOSS) == {"timeout": 2, "resigned": 1}


def test_games_where_the_user_never_moved_are_ignored() -> None:
    resigned_at_once = make_game(time_control=BLITZ, user_color=Color.BLACK)

    assert clock_profile([(resigned_at_once, [299.0])]) is None
