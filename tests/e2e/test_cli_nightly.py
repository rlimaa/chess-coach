from datetime import date
from pathlib import Path

import pytest
import respx
from typer.testing import CliRunner

from chesscoach.interfaces.cli.main import app
from tests.fixtures.chesscom import load

API = "https://api.chess.com/pub/player"
STOCKFISH = Path("/usr/local/bin/stockfish")
runner = CliRunner()


@pytest.fixture(autouse=True)
def _settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("COACH_CONFIG", str(tmp_path / "none.toml"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "coach.db"))
    monkeypatch.setenv("CHESSCOM_USERNAME", "rodigola")
    monkeypatch.setenv("ENGINE__THREADS", "1")


def _mock_chesscom() -> None:
    respx.get(f"{API}/rodigola/games/archives").respond(
        json={"archives": [f"{API}/rodigola/games/2026/09"]}
    )
    respx.get(f"{API}/rodigola/games/2026/09").respond(json=load("month.json"))


def test_nightly_skips_while_another_analysis_holds_the_lock(tmp_path: Path) -> None:
    (tmp_path / ".analysis.lock").mkdir()

    result = runner.invoke(app, ["nightly"])

    assert result.exit_code == 0, result.output
    assert "Skipped" in result.output


def test_scheduler_does_not_record_a_run_it_had_to_skip(tmp_path: Path) -> None:
    (tmp_path / ".analysis.lock").mkdir()

    runner.invoke(app, ["scheduler", "--at", "00:00", "--once"])

    assert not (tmp_path / "scheduler-last-run").exists()


@pytest.mark.slow
@pytest.mark.skipif(not STOCKFISH.exists(), reason="Stockfish binary not available")
@respx.mock
def test_scheduler_runs_the_nightly_job_once_per_day(tmp_path: Path) -> None:
    _mock_chesscom()

    first = runner.invoke(
        app, ["scheduler", "--at", "00:00", "--once", "--games", "1", "--depth", "6"]
    )
    again = runner.invoke(
        app, ["scheduler", "--at", "00:00", "--once", "--games", "1", "--depth", "6"]
    )

    assert first.exit_code == 0, first.output
    assert "Synced rodigola: 6 new games" in first.output
    assert "rapid: analyzed 1" in first.output
    assert "blitz: analyzed 1" in first.output
    assert (tmp_path / "scheduler-last-run").read_text().strip() == date.today().isoformat()
    assert "Synced" not in again.output
