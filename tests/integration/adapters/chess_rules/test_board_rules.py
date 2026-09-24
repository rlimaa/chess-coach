import pytest

from chesscoach.adapters.chess_rules.board_rules import PythonChessRules
from chesscoach.domain.value_objects import Color

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
BACK_RANK = "6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1"


@pytest.mark.parametrize("text", ["Rd8#", "Rd8", "rd8", "d1d8", " Rd8+ "])
def test_accepts_san_or_uci_and_returns_canonical_san(text: str) -> None:
    assert PythonChessRules().normalize_move(BACK_RANK, text) == "Rd8#"


@pytest.mark.parametrize("text", ["Rd9", "Ke4", "", "hello"])
def test_rejects_illegal_or_unreadable_moves(text: str) -> None:
    assert PythonChessRules().normalize_move(BACK_RANK, text) is None


def test_board_is_drawn_from_the_players_side() -> None:
    white_view = PythonChessRules().render(START, Color.WHITE).splitlines()
    black_view = PythonChessRules().render(START, Color.BLACK).splitlines()

    assert white_view[0].startswith("8")
    assert white_view[-1].strip().startswith("a")
    assert black_view[0].startswith("1")
    assert black_view[-1].strip().startswith("h")
    assert "♔" in "".join(white_view)
