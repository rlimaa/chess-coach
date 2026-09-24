import pytest

from chesscoach.domain.services.openings import opening_family, opening_records
from chesscoach.domain.value_objects import Color, Outcome
from tests.builders import make_game


@pytest.mark.parametrize(
    ("name", "family"),
    [
        ("Caro Kann Defense Exchange Variation", "Caro Kann Defense"),
        ("Scotch Game Classical Variation", "Scotch Game"),
        ("Queens Gambit Declined", "Queens Gambit"),
        ("Kings Indian Attack", "Kings Indian Attack"),
        ("Alapin Sicilian Defense", "Alapin Sicilian Defense"),
        ("Saragossa Opening", "Saragossa Opening"),
        ("Bishops Opening Berlin Defense", "Bishops Opening"),
        ("Englund", "Englund"),
        (None, "Unknown"),
    ],
)
def test_opening_family_cuts_the_name_after_its_first_family_word(
    name: str | None, family: str
) -> None:
    assert opening_family(name) == family


def test_records_are_per_color_and_family_most_played_first_with_minimum_games() -> None:
    games = [
        make_game(opening="Caro Kann Defense Exchange Variation", user_color=Color.BLACK),
        make_game(opening="Caro Kann Defense", user_color=Color.BLACK, outcome=Outcome.LOSS),
        make_game(opening="Caro Kann Defense", user_color=Color.WHITE),
        make_game(opening="Scotch Game", user_color=Color.WHITE),
        make_game(opening="Scotch Game Classical Variation", user_color=Color.WHITE),
        make_game(opening="Scotch Game", user_color=Color.WHITE, outcome=Outcome.DRAW),
    ]

    records = opening_records(games, min_games=2)

    assert [(r.color, r.family, r.summary.games) for r in records] == [
        (Color.WHITE, "Scotch Game", 3),
        (Color.BLACK, "Caro Kann Defense", 2),
    ]
    assert records[1].summary.score_pct == 50.0
