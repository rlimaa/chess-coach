from chesscoach.application.dto import TrainingPlan
from chesscoach.application.ports import TrainingPlanSource


class GetTrainingPlan:
    def __init__(self, source: TrainingPlanSource) -> None:
        self._source = source

    def execute(self) -> TrainingPlan | None:
        return self._source.current()
