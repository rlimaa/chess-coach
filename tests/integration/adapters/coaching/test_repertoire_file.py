import json
from pathlib import Path

import pytest

from chesscoach.adapters.coaching.repertoire_file import JsonRepertoireFile
from chesscoach.application.errors import InvalidRepertoireError
from chesscoach.domain.value_objects import Color

ENTRY = {
    "id": "black-italian",
    "title": "Black vs the Italian: 3...Bc5",
    "side": "black",
    "focus": True,
    "line": "e4 e5 Nf3 Nc6 Bc4 Bc5",
    "key_ply": 5,
    "why": "3...Nf6 scored 14%",
    "plan": "...d6, ...Nf6, ...0-0",
    "instead_of": "e4 e5 Nf3 Nc6 Bc4 Nf6 Ng5",
    "instead_result": "14% in 7 games",
}


def _write(tmp_path: Path, data: object) -> Path:
    path = tmp_path / "repertoire.json"
    path.write_text(json.dumps(data))
    return path


def test_entries_are_read_with_moves_split_into_a_line(tmp_path: Path) -> None:
    (entry,) = JsonRepertoireFile(_write(tmp_path, {"lines": [ENTRY]})).entries()

    assert entry.id == "black-italian"
    assert entry.side is Color.BLACK
    assert entry.focus
    assert entry.line == ("e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5")
    assert entry.instead_of == ("e4", "e5", "Nf3", "Nc6", "Bc4", "Nf6", "Ng5")


def test_the_comparison_line_is_optional(tmp_path: Path) -> None:
    minimal = {k: v for k, v in ENTRY.items() if k not in ("instead_of", "instead_result")}

    (entry,) = JsonRepertoireFile(_write(tmp_path, {"lines": [minimal]})).entries()

    assert entry.instead_of == ()
    assert entry.instead_result == ""


def test_no_file_means_no_repertoire(tmp_path: Path) -> None:
    assert JsonRepertoireFile(tmp_path / "missing.json").entries() == []


def test_a_malformed_entry_is_reported(tmp_path: Path) -> None:
    broken = {k: v for k, v in ENTRY.items() if k != "line"}

    with pytest.raises(InvalidRepertoireError, match="black-italian"):
        JsonRepertoireFile(_write(tmp_path, {"lines": [broken]})).entries()
