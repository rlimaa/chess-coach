from datetime import date, datetime, time


def is_due(now: datetime, at: time, last_run: date | None) -> bool:
    return now.time() >= at and last_run != now.date()
