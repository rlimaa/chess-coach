import os
import time
from datetime import timedelta
from pathlib import Path

from chesscoach.adapters.locking.directory_lock import DirectoryLock

HALF_DAY = timedelta(hours=12)


def test_lock_is_taken_and_released(tmp_path: Path) -> None:
    lock = DirectoryLock(tmp_path / ".analysis.lock", max_age=HALF_DAY)

    with lock.hold() as acquired:
        assert acquired
        assert (tmp_path / ".analysis.lock").is_dir()

    assert not (tmp_path / ".analysis.lock").exists()


def test_a_fresh_lock_held_elsewhere_is_respected(tmp_path: Path) -> None:
    (tmp_path / ".analysis.lock").mkdir()

    with DirectoryLock(tmp_path / ".analysis.lock", max_age=HALF_DAY).hold() as acquired:
        assert not acquired

    assert (tmp_path / ".analysis.lock").is_dir()


def test_a_stale_lock_is_taken_over(tmp_path: Path) -> None:
    stale = tmp_path / ".analysis.lock"
    stale.mkdir()
    old = time.time() - 13 * 3600
    os.utime(stale, (old, old))

    with DirectoryLock(stale, max_age=HALF_DAY).hold() as acquired:
        assert acquired
