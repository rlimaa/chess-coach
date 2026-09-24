from pathlib import Path

import pytest
import respx
from typer.testing import CliRunner

from chesscoach.adapters.persistence.sqlite.analysis_repository import SqliteAnalysisRepository
from chesscoach.adapters.persistence.sqlite.database import SqliteDatabase
from chesscoach.domain.value_objects import Color, MoveClass
from chesscoach.interfaces.cli.main import app
from tests.builders import make_analysis, make_game, make_move
from tests.fixtures.chesscom import load, month_game

API = "https://api.chess.com/pub/player"
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
BLITZ_WIN_AS_WHITE = month_game(0)
runner = CliRunner()


@pytest.fixture(autouse=True)
def _synced_with_one_blunder(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    db_path = tmp_path / "coach.db"
    monkeypatch.setenv("COACH_CONFIG", str(tmp_path / "none.toml"))
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("CHESSCOM_USERNAME", "rodigola")
    with respx.mock:
        respx.get(f"{API}/rodigola/games/archives").respond(
            json={"archives": [f"{API}/rodigola/games/2026/09"]}
        )
        respx.get(f"{API}/rodigola/games/2026/09").respond(json=load("month.json"))
        runner.invoke(app, ["sync"])
    blunder = make_move(
        color=Color.WHITE,
        fen_before=START,
        san="a3",
        best_move_san="e4",
        move_class=MoveClass.BLUNDER,
        win_pct_loss=20.0,
    )
    game = make_game(id=BLITZ_WIN_AS_WHITE["uuid"])
    SqliteAnalysisRepository(SqliteDatabase(db_path)).save(make_analysis(game, blunder))


def test_solving_a_puzzle_then_it_rests() -> None:
    first = runner.invoke(app, ["puzzles", "-t", "blitz", "-n", "1"], input="e4\n")
    again = runner.invoke(app, ["puzzles", "-t", "blitz", "-n", "1"])

    assert first.exit_code == 0, first.output
    assert "a3" in first.output
    assert "Correct" in first.output
    assert "1/1 solved" in first.output
    assert "No puzzles due" in again.output


def test_wrong_and_illegal_answers() -> None:
    result = runner.invoke(app, ["puzzles", "-n", "1"], input="Ke5\nd4\n")

    assert result.exit_code == 0, result.output
    assert "not a legal move" in result.output
    assert "best was e4" in result.output
    assert "0/1 solved" in result.output


def test_listing_puzzles_is_not_interactive() -> None:
    result = runner.invoke(app, ["puzzles", "--list"])

    assert result.exit_code == 0, result.output
    assert START in result.output
    assert "e4" not in result.output.replace(START, "")


def test_progress_compares_periods() -> None:
    result = runner.invoke(app, ["progress", "-t", "blitz", "--days", "3650"])

    assert result.exit_code == 0, result.output
    assert "Score" in result.output
    assert "Rating change" in result.output
