import json
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).parent


def load(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((FIXTURES / name).read_text())
    return data


def month_game(index: int) -> dict[str, Any]:
    game: dict[str, Any] = load("month.json")["games"][index]
    return game
