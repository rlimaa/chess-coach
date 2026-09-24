from dataclasses import replace

import pytest

from chesscoach.application.dto import RepertoireEntry
from chesscoach.application.errors import InvalidRepertoireError
from chesscoach.application.use_cases.repertoire import GetRepertoire
from chesscoach.domain.value_objects import Color
from tests.fakes import FakeChessRules, FakeRepertoire

GIUOCO = RepertoireEntry(
    id="black-italian",
    title="Black vs the Italian: 3...Bc5",
    side=Color.BLACK,
    focus=True,
    line=("e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5"),
    key_ply=5,
    why="3...Nf6 scored 14% in the Fried Liver",
    plan="...d6, ...Nf6, ...0-0",
    instead_of=("e4", "e5", "Nf3", "Nc6", "Bc4", "Nf6", "Ng5"),
    instead_result="14% in 7 games",
)


def _repertoire(*entries: RepertoireEntry) -> GetRepertoire:
    return GetRepertoire(FakeRepertoire(list(entries)), FakeChessRules({}))


def test_lines_are_expanded_into_positions_for_the_board() -> None:
    (opening,) = _repertoire(GIUOCO).execute()

    assert opening.entry == GIUOCO
    assert [m.san for m in opening.moves] == list(GIUOCO.line)
    assert opening.moves[0].fen_after == "fen-0"
    assert [m.san for m in opening.old_moves] == list(GIUOCO.instead_of)


def test_focus_lines_come_first() -> None:
    later = replace(GIUOCO, id="later", focus=False)

    openings = _repertoire(later, GIUOCO).execute()

    assert [o.entry.id for o in openings] == ["black-italian", "later"]


def test_an_illegal_move_names_the_broken_line() -> None:
    broken = replace(GIUOCO, line=("e4", "??"))

    with pytest.raises(InvalidRepertoireError, match="black-italian"):
        _repertoire(broken).execute()


def test_the_key_move_must_be_inside_the_line() -> None:
    broken = replace(GIUOCO, key_ply=6)

    with pytest.raises(InvalidRepertoireError, match="key_ply"):
        _repertoire(broken).execute()
