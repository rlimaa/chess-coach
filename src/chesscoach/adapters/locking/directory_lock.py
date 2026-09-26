import shutil
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path


class DirectoryLock:
    """mkdir is atomic on every filesystem the host and the containers share, unlike pid files."""

    def __init__(self, path: Path, *, max_age: timedelta) -> None:
        self._path = path
        self._max_age = max_age

    @contextmanager
    def hold(self) -> Iterator[bool]:
        if not self._acquire():
            yield False
            return
        try:
            yield True
        finally:
            shutil.rmtree(self._path, ignore_errors=True)

    def _acquire(self) -> bool:
        try:
            self._path.mkdir(parents=True)
            return True
        except FileExistsError:
            if time.time() - self._path.stat().st_mtime < self._max_age.total_seconds():
                return False
            shutil.rmtree(self._path, ignore_errors=True)
            return self._acquire()
