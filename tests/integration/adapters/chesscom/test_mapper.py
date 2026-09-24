from copy import deepcopy
from datetime import UTC, datetime

from chesscoach.adapters.chesscom.mapper import to_game
from chesscoach.domain.entities import Accuracies, PlayerSide
from chesscoach.domain.value_objects import Color, Outcome, TimeClass
from tests.fixtures.chesscom import month_game

DAILY_WHITE_WIN = 4
RAPID_BLACK_LOSS = 2


def test_maps_a_reviewed_daily_game_won_with_white() -> None:
    raw = month_game(DAILY_WHITE_WIN)

    game = to_game(raw, "rodigola")

    assert game is not None
    assert game.id == raw["uuid"]
    assert game.url == "https://www.chess.com/game/daily/1006634576"
    assert game.played_at == datetime.fromtimestamp(1785675975, tz=UTC)
    assert game.time_class is TimeClass.DAILY
    assert str(game.time_control) == "1/259200"
    assert game.rated
    assert game.white == PlayerSide("rodigola", 1406)
    assert game.black == PlayerSide("BMP2026", 1080)
    assert game.user_color is Color.WHITE
    assert game.outcome is Outcome.WIN
    assert game.termination == "resigned"
    assert game.eco == "C45"
    assert game.opening == "Scotch Game"
    assert game.accuracies == Accuracies(white=57.54, black=51.06)
    assert game.pgn == raw["pgn"]


def test_maps_a_loss_with_black_without_accuracies() -> None:
    game = to_game(month_game(RAPID_BLACK_LOSS), "rodigola")

    assert game is not None
    assert game.user_color is Color.BLACK
    assert game.outcome is Outcome.LOSS
    assert game.termination == "checkmated"
    assert game.accuracies is None


def test_username_match_is_case_insensitive() -> None:
    game = to_game(month_game(DAILY_WHITE_WIN), "RoDiGoLa")

    assert game is not None
    assert game.user_color is Color.WHITE


def test_agreed_result_is_a_draw() -> None:
    raw = deepcopy(month_game(DAILY_WHITE_WIN))
    raw["white"]["result"] = raw["black"]["result"] = "agreed"

    game = to_game(raw, "rodigola")

    assert game is not None
    assert game.outcome is Outcome.DRAW
    assert game.termination == "agreed"


def test_variant_games_are_skipped() -> None:
    raw = deepcopy(month_game(DAILY_WHITE_WIN))
    raw["rules"] = "chess960"

    assert to_game(raw, "rodigola") is None
