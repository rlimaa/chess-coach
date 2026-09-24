import os
from pathlib import Path

import pytest

from chesscoach.config import Settings, load_settings

SETTINGS_ENV_PREFIXES = (*(name.upper() for name in Settings.model_fields), "COACH_CONFIG")


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # The dev container loads .env, so clear anything that could leak into settings.
    for name in list(os.environ):
        if name.upper().startswith(SETTINGS_ENV_PREFIXES):
            monkeypatch.delenv(name)
    monkeypatch.chdir(tmp_path)


def test_defaults_apply_when_no_config_file_or_env() -> None:
    settings = load_settings(config_file=Path("missing.toml"))

    assert settings.chesscom_username == ""
    assert settings.db_path == Path("data/coach.db")
    assert settings.engine.path == Path("/usr/local/bin/stockfish")
    assert settings.engine.depth == 16


def test_config_file_values_override_defaults() -> None:
    Path("config.toml").write_text('chesscom_username = "from_file"\n[engine]\ndepth = 20\n')

    settings = load_settings(config_file=Path("config.toml"))

    assert settings.chesscom_username == "from_file"
    assert settings.engine.depth == 20
    assert settings.engine.threads == 2


def test_environment_overrides_config_file(monkeypatch: pytest.MonkeyPatch) -> None:
    Path("config.toml").write_text('chesscom_username = "from_file"\n[engine]\nthreads = 1\n')
    monkeypatch.setenv("CHESSCOM_USERNAME", "from_env")
    monkeypatch.setenv("ENGINE__THREADS", "8")

    settings = load_settings(config_file=Path("config.toml"))

    assert settings.chesscom_username == "from_env"
    assert settings.engine.threads == 8


def test_config_file_location_can_come_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    Path("elsewhere.toml").write_text('contact_email = "me@example.com"\n')
    monkeypatch.setenv("COACH_CONFIG", "elsewhere.toml")

    assert load_settings().contact_email == "me@example.com"
