from chesscoach.domain.services.phase_detection import detect_phase
from chesscoach.domain.value_objects import Phase

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
MIDDLEGAME = "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N2N2/PP2BPPP/R2QKB1R w KQ - 0 12"
ROOK_ENDGAME = "8/5pk1/6p1/8/3R4/6P1/r4PK1/8 w - - 0 40"


def test_early_moves_with_full_material_are_opening() -> None:
    assert detect_phase(ply=0, fen=START) is Phase.OPENING


def test_later_moves_with_many_pieces_are_middlegame() -> None:
    assert detect_phase(ply=22, fen=MIDDLEGAME) is Phase.MIDDLEGAME


def test_few_pieces_left_is_endgame_even_early() -> None:
    assert detect_phase(ply=18, fen=ROOK_ENDGAME) is Phase.ENDGAME
