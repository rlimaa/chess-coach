from chesscoach.domain.entities import Accuracies, PlayerSide
from chesscoach.domain.value_objects import Color
from tests.builders import make_game


def test_game_exposes_user_and_opponent_by_color() -> None:
    game = make_game(
        white=PlayerSide("rival", 1600),
        black=PlayerSide("me", 1550),
        user_color=Color.BLACK,
        accuracies=Accuracies(white=91.5, black=78.2),
    )

    assert game.user == PlayerSide("me", 1550)
    assert game.opponent == PlayerSide("rival", 1600)
    assert game.user_accuracy == 78.2


def test_user_accuracy_is_none_when_game_was_not_reviewed() -> None:
    assert make_game(accuracies=None).user_accuracy is None
