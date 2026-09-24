import json
from pathlib import Path
from typing import Any

from chesscoach.application.dto import RepertoireEntry
from chesscoach.application.errors import InvalidRepertoireError
from chesscoach.domain.value_objects import Color


class JsonRepertoireFile:
    def __init__(self, path: Path) -> None:
        self._path = path

    def entries(self) -> list[RepertoireEntry]:
        if not self._path.is_file():
            return []
        lines: list[dict[str, Any]] = json.loads(self._path.read_text())["lines"]
        return [_entry(raw) for raw in lines]


def _entry(raw: dict[str, Any]) -> RepertoireEntry:
    try:
        return RepertoireEntry(
            id=raw["id"],
            title=raw["title"],
            side=Color(raw["side"]),
            focus=bool(raw.get("focus", False)),
            line=tuple(raw["line"].split()),
            key_ply=int(raw["key_ply"]),
            why=raw["why"],
            plan=raw["plan"],
            instead_of=tuple(raw.get("instead_of", "").split()),
            instead_result=raw.get("instead_result", ""),
        )
    except (KeyError, ValueError) as error:
        raise InvalidRepertoireError(f"{raw.get('id', '?')}: missing or invalid {error}") from error
