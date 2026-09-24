from pathlib import Path

import pytest
import respx
from typer.testing import CliRunner

from chesscoach.interfaces.cli.main import app
from tests.fixtures.chesscom import load, month_game

API = "https://api.chess.com/pub/player"
STOCKFISH = Path("/usr/local/bin/stockfish")
NEWEST_GAME = month_game(0)
runner = CliRunner()

needs_engine = pytest.mark.skipif(not STOCKFISH.exists(), reason="Stockfish binary not available")


@pytest.fixture(autouse=True)
def _synced(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("COACH_CONFIG", str(tmp_path / "none.toml"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "coach.db"))
    monkeypatch.setenv("CHESSCOM_USERNAME", "rodigola")
    monkeypatch.setenv("ENGINE__THREADS", "1")
    with respx.mock:
        respx.get(f"{API}/rodigola/games/archives").respond(
            json={"archives": [f"{API}/rodigola/games/2026/09"]}
        )
        respx.get(f"{API}/rodigola/games/2026/09").respond(json=load("month.json"))
        runner.invoke(app, ["sync"])


@pytest.mark.slow
@needs_engine
def test_analyze_then_review_a_game() -> None:
    analyzed = runner.invoke(app, ["analyze", "--last", "1", "--depth", "6"])
    review = runner.invoke(app, ["game", NEWEST_GAME["url"]])

    assert analyzed.exit_code == 0, analyzed.output
    assert "Analyzed 1 game" in analyzed.output
    assert "5 still pending" in analyzed.output
    assert review.exit_code == 0, review.output
    assert "Accuracy" in review.output
    assert "depth 6" in review.output


def test_reviewing_an_unanalyzed_game_explains_what_to_do() -> None:
    result = runner.invoke(app, ["game", NEWEST_GAME["uuid"]])

    assert result.exit_code == 1
    assert "coach analyze" in result.output


def test_reviewing_an_unknown_game_fails_clearly() -> None:
    result = runner.invoke(app, ["game", "does-not-exist"])

    assert result.exit_code == 1
    assert "not found" in result.output.lower()
