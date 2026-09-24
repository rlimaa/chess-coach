from pathlib import Path

import pytest
from typer.testing import CliRunner

from chesscoach.interfaces.cli.main import app

runner = CliRunner()


def test_help_lists_engine_check_command() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "engine-check" in result.output


def test_engine_check_reports_a_helpful_error_when_engine_is_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("ENGINE__PATH", str(tmp_path / "no-engine"))

    result = runner.invoke(app, ["engine-check"])

    assert result.exit_code == 1
    assert "not found" in result.output


@pytest.mark.slow
@pytest.mark.skipif(
    not Path("/usr/local/bin/stockfish").exists(), reason="Stockfish binary not available"
)
def test_engine_check_shows_engine_name_and_evaluation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENGINE__PATH", "/usr/local/bin/stockfish")

    result = runner.invoke(app, ["engine-check"])

    assert result.exit_code == 0
    assert "Stockfish" in result.output
    assert "Best move" in result.output
