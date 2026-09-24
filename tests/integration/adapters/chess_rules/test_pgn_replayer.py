import pytest

from chesscoach.adapters.chess_rules.pgn_replayer import PgnReplayer
from chesscoach.application.errors import InvalidGameError
from chesscoach.domain.value_objects import Color
from tests.fixtures.chesscom import month_game

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def test_replays_every_ply_with_position_before_the_move_and_clock() -> None:
    game = PgnReplayer().replay(
        "1. e4 {[%clk 0:02:59.9]} 1... e5 {[%clk 0:02:58]} 2. Nf3 {[%clk 0:02:57]} *"
    )

    first, second, third = game.plies
    assert (first.index, first.color, first.san, first.uci) == (0, Color.WHITE, "e4", "e2e4")
    assert first.fen_before == START
    assert first.clock_seconds == pytest.approx(179.9)
    assert (second.color, second.san, second.clock_seconds) == (Color.BLACK, "e5", 178.0)
    assert third.index == 2
    assert game.final_fen.startswith("rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b")


def test_moves_without_clock_annotations_have_no_clock() -> None:
    assert PgnReplayer().replay("1. d4 d5 *").plies[0].clock_seconds is None


def test_replays_a_real_chesscom_game_to_its_final_position() -> None:
    raw = month_game(4)

    game = PgnReplayer().replay(raw["pgn"])

    assert game.final_fen.split(" ")[0] == raw["fen"].split(" ")[0]
    assert game.plies[0].san == "e4"


def test_illegal_moves_are_rejected() -> None:
    with pytest.raises(InvalidGameError):
        PgnReplayer().replay("1. e4 e5 2. Ke3 Qh4 3. Kxh8 *")
