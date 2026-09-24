from datetime import UTC, datetime
from pathlib import Path

from chesscoach.application.dto import TrainingPlan


class MarkdownTrainingPlanFile:
    def __init__(self, path: Path) -> None:
        self._path = path

    def current(self) -> TrainingPlan | None:
        if not self._path.is_file():
            return None
        updated_at = datetime.fromtimestamp(self._path.stat().st_mtime, tz=UTC)
        return TrainingPlan(self._path.read_text(), updated_at)
