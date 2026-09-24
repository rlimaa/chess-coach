from chesscoach.domain.value_objects import Phase

_OPENING_PLIES = 20
_OPENING_MIN_PIECES = 11
_ENDGAME_MAX_PIECES = 6
_NON_PAWN_PIECES = frozenset("nbrqNBRQ")


def detect_phase(ply: int, fen: str) -> Phase:
    """Phase by minor+major pieces left (kings and pawns excluded), then by move number."""
    pieces = sum(char in _NON_PAWN_PIECES for char in fen.split(" ", 1)[0])
    if pieces <= _ENDGAME_MAX_PIECES:
        return Phase.ENDGAME
    if ply < _OPENING_PLIES and pieces >= _OPENING_MIN_PIECES:
        return Phase.OPENING
    return Phase.MIDDLEGAME
