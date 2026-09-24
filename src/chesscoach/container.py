"""Composition root: the only place that builds concrete adapters from settings."""

from chesscoach.adapters.engine.diagnostics import EngineProbe, probe_engine
from chesscoach.config import Settings

ENGINE_CHECK_DEPTH = 12


class Container:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def probe_engine(self) -> EngineProbe:
        return probe_engine(self._settings.engine.path, depth=ENGINE_CHECK_DEPTH)
