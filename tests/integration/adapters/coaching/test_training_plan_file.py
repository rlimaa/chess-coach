import os
from datetime import UTC, datetime
from pathlib import Path

from chesscoach.adapters.coaching.training_plan_file import MarkdownTrainingPlanFile


def test_reads_the_plan_with_its_last_update_time(tmp_path: Path) -> None:
    plan_file = tmp_path / "training_plan.md"
    plan_file.write_text("# Plan\n\n- Keep 50% of the clock at move 20\n")
    stamp = datetime(2026, 9, 24, 18, 30, tzinfo=UTC).timestamp()
    os.utime(plan_file, (stamp, stamp))

    plan = MarkdownTrainingPlanFile(plan_file).current()

    assert plan is not None
    assert plan.markdown.startswith("# Plan")
    assert plan.updated_at == datetime(2026, 9, 24, 18, 30, tzinfo=UTC)


def test_no_plan_file_means_no_plan(tmp_path: Path) -> None:
    assert MarkdownTrainingPlanFile(tmp_path / "missing.md").current() is None
