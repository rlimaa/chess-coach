from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from chesscoach.application.scheduling import is_due

SAO_PAULO = ZoneInfo("America/Sao_Paulo")
AT = time(20, 0)


def _at(hour: int, minute: int = 0, day: int = 26) -> datetime:
    return datetime(2026, 9, day, hour, minute, tzinfo=SAO_PAULO)


def test_not_due_before_the_scheduled_time() -> None:
    assert not is_due(_at(19, 59), AT, last_run=date(2026, 9, 25))


def test_due_at_or_after_the_scheduled_time_if_not_run_today() -> None:
    assert is_due(_at(20, 0), AT, last_run=date(2026, 9, 25))
    assert is_due(_at(23, 10), AT, last_run=None)


def test_runs_only_once_per_day() -> None:
    assert not is_due(_at(21, 0), AT, last_run=date(2026, 9, 26))


def test_a_run_missed_while_asleep_happens_on_wake_the_same_evening() -> None:
    assert is_due(_at(22, 45), AT, last_run=date(2026, 9, 24))
