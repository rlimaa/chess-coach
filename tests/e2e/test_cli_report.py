from pathlib import Path

import pytest
import respx
from typer.testing import CliRunner

from chesscoach.interfaces.cli.main import app
from tests.fixtures.chesscom import load

API = "https://api.chess.com/pub/player"
runner = CliRunner()


@pytest.fixture(autouse=True)
def _synced(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("COACH_CONFIG", str(tmp_path / "none.toml"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "coach.db"))
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path / "reports"))
    monkeypatch.setenv("CHESSCOM_USERNAME", "rodigola")
    with respx.mock:
        respx.get(f"{API}/rodigola/games/archives").respond(
            json={"archives": [f"{API}/rodigola/games/2026/09"]}
        )
        respx.get(f"{API}/rodigola/games/2026/09").respond(json=load("month.json"))
        runner.invoke(app, ["sync"])


def test_report_writes_rapid_and_blitz_by_default(tmp_path: Path) -> None:
    result = runner.invoke(app, ["report"])

    assert result.exit_code == 0, result.output
    written = sorted(p.name.split("-", 3)[-1] for p in (tmp_path / "reports").glob("*.md"))
    assert written == ["blitz.md", "rapid.md"]
    assert "rapid" in result.output
    assert "blitz" in result.output


def test_report_can_target_one_time_class(tmp_path: Path) -> None:
    result = runner.invoke(app, ["report", "--time-class", "daily"])

    assert result.exit_code == 0, result.output
    assert [p.name.endswith("daily.md") for p in (tmp_path / "reports").glob("*.md")] == [True]
