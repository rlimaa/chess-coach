import pytest

from chesscoach.domain.value_objects import TimeControl


@pytest.mark.parametrize(
    ("raw", "base", "increment"),
    [("600", 600, 0), ("180+2", 180, 2), ("60", 60, 0)],
)
def test_live_time_control_has_base_and_increment(raw: str, base: int, increment: int) -> None:
    control = TimeControl.parse(raw)

    assert control.base_seconds == base
    assert control.increment_seconds == increment
    assert not control.is_correspondence


def test_daily_time_control_is_correspondence_with_seconds_per_move() -> None:
    control = TimeControl.parse("1/86400")

    assert control.is_correspondence
    assert control.base_seconds == 86400
    assert str(control) == "1/86400"
