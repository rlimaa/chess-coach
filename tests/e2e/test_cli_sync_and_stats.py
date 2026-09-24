from pathlib import Path

import pytest
import respx
from typer.testing import CliRunner

from chesscoach.interfaces.cli.main import app
from tests.fixtures.chesscom import load

API = "https://api.chess.com/pub/player"
runner = CliRunner()


@pytest.fixture(autouse=True)
def _settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("COACH_CONFIG", str(tmp_path / "none.toml"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "coach.db"))
    monkeypatch.setenv("CHESSCOM_USERNAME", "rodigola")
    monkeypatch.setenv("CONTACT_EMAIL", "me@example.com")


def _mock_chesscom() -> None:
    respx.get(f"{API}/rodigola/games/archives").respond(
        json={"archives": [f"{API}/rodigola/games/2026/09"]}
    )
    respx.get(f"{API}/rodigola/games/2026/09").respond(json=load("month.json"))


@respx.mock
def test_sync_imports_games_and_is_idempotent() -> None:
    _mock_chesscom()

    first = runner.invoke(app, ["sync"])
    second = runner.invoke(app, ["sync"])

    assert first.exit_code == 0, first.output
    assert "6 new games" in first.output
    assert "0 new games" in second.output


@respx.mock
def test_stats_show_results_per_time_class_after_sync() -> None:
    _mock_chesscom()
    runner.invoke(app, ["sync"])

    result = runner.invoke(app, ["stats"])

    assert result.exit_code == 0, result.output
    assert "rodigola" in result.output
    for time_class in ("blitz", "rapid", "bullet", "daily"):
        assert time_class in result.output


def test_sync_explains_missing_username(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHESSCOM_USERNAME", "")

    result = runner.invoke(app, ["sync"])

    assert result.exit_code == 1
    assert "CHESSCOM_USERNAME" in result.output


@respx.mock
def test_sync_reports_unknown_player() -> None:
    respx.get(f"{API}/ghost/games/archives").respond(404)

    result = runner.invoke(app, ["sync", "--username", "ghost"])

    assert result.exit_code == 1
    assert "not found" in result.output.lower()
