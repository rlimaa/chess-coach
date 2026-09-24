"""Application settings.

Precedence: environment variables > TOML config file > defaults.
Only the composition root and interfaces read settings; adapters receive plain values.
"""

import os
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

DEFAULT_CONFIG_FILE = Path("config.toml")


class EngineSettings(BaseModel):
    path: Path = Path("/usr/local/bin/stockfish")
    depth: int = 16
    threads: int = 2
    hash_mb: int = 256


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__", extra="ignore")

    chesscom_username: str = ""
    contact_email: str = ""
    db_path: Path = Path("data/coach.db")
    reports_dir: Path = Path("reports")
    timezone: ZoneInfo = ZoneInfo("UTC")
    engine: EngineSettings = EngineSettings()


def load_settings(config_file: Path | None = None) -> Settings:
    toml_file = config_file or Path(os.environ.get("COACH_CONFIG", DEFAULT_CONFIG_FILE))

    class _FileBackedSettings(Settings):
        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            toml_settings = TomlConfigSettingsSource(settings_cls, toml_file=toml_file)
            return init_settings, env_settings, toml_settings

    return _FileBackedSettings()
