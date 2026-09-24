from pathlib import Path

import pytest

from chesscoach.adapters.engine.diagnostics import probe_engine

STOCKFISH = Path("/usr/local/bin/stockfish")

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not STOCKFISH.exists(), reason="Stockfish binary not available"),
]


def test_probe_identifies_engine_and_evaluates_start_position() -> None:
    probe = probe_engine(STOCKFISH, depth=8)

    assert probe.name.startswith("Stockfish")
    assert probe.best_move
    assert probe.score_cp is not None
    assert abs(probe.score_cp) < 100


def test_probe_fails_clearly_when_binary_is_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="nope"):
        probe_engine(tmp_path / "nope", depth=1)
