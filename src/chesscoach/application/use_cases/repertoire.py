from collections.abc import Sequence

from chesscoach.application.dto import LineMove, OpeningLine, RepertoireEntry
from chesscoach.application.errors import InvalidMoveError, InvalidRepertoireError
from chesscoach.application.ports import ChessRules, RepertoireSource


class GetRepertoire:
    def __init__(self, source: RepertoireSource, rules: ChessRules) -> None:
        self._source = source
        self._rules = rules

    def execute(self) -> list[OpeningLine]:
        openings = [self._expand(entry) for entry in self._source.entries()]
        return sorted(openings, key=lambda o: not o.entry.focus)

    def _expand(self, entry: RepertoireEntry) -> OpeningLine:
        if not 0 <= entry.key_ply < len(entry.line):
            raise InvalidRepertoireError(f"{entry.id}: key_ply {entry.key_ply} is outside the line")
        return OpeningLine(
            entry, self._play(entry, entry.line), self._play(entry, entry.instead_of)
        )

    def _play(self, entry: RepertoireEntry, moves: Sequence[str]) -> tuple[LineMove, ...]:
        try:
            return self._rules.play_line(moves)
        except InvalidMoveError as error:
            raise InvalidRepertoireError(f"{entry.id}: {error}") from error
