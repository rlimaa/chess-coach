import pytest

from chesscoach.adapters.chess_rules.clock_reader import PgnClockReader
from tests.fixtures.chesscom import month_game


def test_reads_every_clock_annotation_in_order() -> None:
    pgn = "1. e4 {[%clk 0:02:59.9]} 1... e5 {[%clk 0:02:58]} 2. Nf3 {[%clk 1:00:00]} *"

    assert PgnClockReader().clocks(pgn) == pytest.approx([179.9, 178.0, 3600.0])


def test_pgn_without_clocks_has_none() -> None:
    assert list(PgnClockReader().clocks("1. e4 e5 *")) == []


def test_reads_a_real_chesscom_game() -> None:
    clocks = PgnClockReader().clocks(month_game(0)["pgn"])

    assert len(clocks) > 10
    assert all(c >= 0 for c in clocks)
