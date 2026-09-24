import calendar
from collections import defaultdict
from collections.abc import Iterable
from datetime import timedelta
from zoneinfo import ZoneInfo

from chesscoach.domain.entities import Game
from chesscoach.domain.insights import DayPart, LabelledSummary, StreakImpact
from chesscoach.domain.services.statistics import ResultSummary, summarize
from chesscoach.domain.value_objects import Outcome

SITTING_GAP = timedelta(hours=1)
TILT_STREAK = 2
_SESSION_BUCKETS = (
    ("1st game", 1, 1),
    ("games 2-3", 2, 3),
    ("games 4-6", 4, 6),
    ("game 7+", 7, None),
)
_DAY_PARTS = (DayPart.NIGHT, DayPart.MORNING, DayPart.AFTERNOON, DayPart.EVENING)


def _sittings(games: Iterable[Game]) -> list[list[Game]]:
    sittings: list[list[Game]] = []
    for game in sorted(games, key=lambda g: g.played_at):
        if sittings and game.played_at - sittings[-1][-1].played_at <= SITTING_GAP:
            sittings[-1].append(game)
        else:
            sittings.append([game])
    return sittings


def streak_impact(games: Iterable[Game]) -> StreakImpact:
    fresh, after_win, after_loss, after_two_losses = [], [], [], []
    for sitting in _sittings(games):
        fresh.append(sitting[0])
        for position, game in enumerate(sitting[1:], start=1):
            previous = sitting[position - 1].outcome
            if previous is Outcome.WIN:
                after_win.append(game)
            elif previous is Outcome.LOSS:
                after_loss.append(game)
                streak = sitting[position - TILT_STREAK : position]
                if len(streak) == TILT_STREAK and all(g.outcome is Outcome.LOSS for g in streak):
                    after_two_losses.append(game)
    return StreakImpact(
        fresh=summarize(fresh),
        after_win=summarize(after_win),
        after_loss=summarize(after_loss),
        after_two_plus_losses=summarize(after_two_losses),
    )


def by_session_position(games: Iterable[Game]) -> list[LabelledSummary]:
    positioned = [(n, g) for s in _sittings(games) for n, g in enumerate(s, start=1)]
    return [
        LabelledSummary(label, summarize(g for n, g in positioned if low <= n <= (high or n)))
        for label, low, high in _SESSION_BUCKETS
    ]


def by_day_part(games: Iterable[Game], tz: ZoneInfo) -> dict[DayPart, ResultSummary]:
    groups: dict[DayPart, list[Game]] = defaultdict(list)
    for game in games:
        groups[_DAY_PARTS[game.played_at.astimezone(tz).hour // 6]].append(game)
    return {part: summarize(groups[part]) for part in _DAY_PARTS}


def by_weekday(games: Iterable[Game], tz: ZoneInfo) -> list[LabelledSummary]:
    groups: dict[int, list[Game]] = defaultdict(list)
    for game in games:
        groups[game.played_at.astimezone(tz).weekday()].append(game)
    return [LabelledSummary(calendar.day_name[day], summarize(groups[day])) for day in range(7)]
