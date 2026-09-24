"""Anti-corruption layer: chess.com game JSON -> domain Game."""

import re
from datetime import UTC, datetime
from typing import Any

from chesscoach.domain.entities import Accuracies, Game, PlayerSide
from chesscoach.domain.value_objects import Color, Outcome, TimeClass, TimeControl

STANDARD_RULES = "chess"
DRAW_RESULTS = frozenset(
    {"agreed", "repetition", "stalemate", "insufficient", "50move", "timevsinsufficient"}
)
_ECO_HEADER = re.compile(r'^\[ECO "([^"]+)"\]$', re.MULTILINE)


def to_game(raw: dict[str, Any], username: str) -> Game | None:
    if raw["rules"] != STANDARD_RULES:
        return None

    white, black = raw["white"], raw["black"]
    user_color = Color.WHITE if white["username"].lower() == username.lower() else Color.BLACK
    user, opponent = (white, black) if user_color is Color.WHITE else (black, white)
    outcome, termination = _outcome(user["result"], opponent["result"])
    accuracies = raw.get("accuracies")

    return Game(
        id=raw["uuid"],
        url=raw["url"],
        played_at=datetime.fromtimestamp(raw["end_time"], tz=UTC),
        time_class=TimeClass(raw["time_class"]),
        time_control=TimeControl.parse(raw["time_control"]),
        rated=raw["rated"],
        white=PlayerSide(white["username"], white["rating"]),
        black=PlayerSide(black["username"], black["rating"]),
        user_color=user_color,
        outcome=outcome,
        termination=termination,
        eco=match.group(1) if (match := _ECO_HEADER.search(raw["pgn"])) else None,
        opening=_opening_name(raw.get("eco")),
        pgn=raw["pgn"],
        accuracies=Accuracies(accuracies["white"], accuracies["black"]) if accuracies else None,
    )


def _outcome(user_result: str, opponent_result: str) -> tuple[Outcome, str]:
    if user_result in DRAW_RESULTS:
        return Outcome.DRAW, user_result
    if user_result == "win":
        return Outcome.WIN, opponent_result
    return Outcome.LOSS, user_result


def _opening_name(eco_url: str | None) -> str | None:
    """'.../openings/Scotch-Game-3...exd4-4.Nxd4' -> 'Scotch Game' (drop the move sequence)."""
    if not eco_url:
        return None
    words: list[str] = []
    for token in eco_url.rstrip("/").rsplit("/", 1)[-1].split("-"):
        if any(char.isdigit() for char in token):
            break
        words.append(token)
    return " ".join(words) or None
