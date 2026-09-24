"""Turn insights into ranked coaching highlights. Thresholds favour signal over noise."""

import math

from chesscoach.domain.insights import Highlight, TimeClassInsights
from chesscoach.domain.services.statistics import ResultSummary

MIN_GAMES = 20
MIN_BUCKET_GAMES = 30
NOTABLE_GAP_PCT = 8.0
TIME_TROUBLE_SHARE_PCT = 20.0
TIME_LOSS_SHARE_PCT = 25.0
NOTABLE_RATING_CHANGE = 25
TREND_MONTHS = 3


def find_highlights(insights: TimeClassInsights) -> list[Highlight]:
    highlights = [
        *_openings(insights),
        *_tilt(insights),
        *_sessions(insights),
        *_day_parts(insights),
        *_clock(insights),
        *_opponents(insights),
        *_rating_trend(insights),
    ]
    return sorted(highlights, key=lambda h: h.severity, reverse=True)


def _severity(gap_pct: float, games: int) -> float:
    return abs(gap_pct) * math.sqrt(games) / 10


def _pct(value: float) -> str:
    return f"{value:.0f}%"


def _underperforms(bucket: ResultSummary, reference: ResultSummary, min_games: int) -> bool:
    return bucket.games >= min_games and bucket.score_pct <= reference.score_pct - NOTABLE_GAP_PCT


def _openings(insights: TimeClassInsights) -> list[Highlight]:
    average = insights.overall.score_pct
    highlights = []
    for record in insights.openings:
        score, games = record.summary.score_pct, record.summary.games
        gap = score - average
        if games < MIN_GAMES or abs(gap) < NOTABLE_GAP_PCT:
            continue
        verdict = "is a strength" if gap > 0 else "is costing you points"
        highlights.append(
            Highlight(
                severity=_severity(gap, games),
                text=f"As {record.color.value}, the {record.family} {verdict}: "
                f"{_pct(score)} over {games} games (your average {_pct(average)}).",
                strength=gap > 0,
            )
        )
    return highlights


def _tilt(insights: TimeClassInsights) -> list[Highlight]:
    after = insights.streaks.after_two_plus_losses
    if not _underperforms(after, insights.overall, MIN_GAMES):
        return []
    return [
        Highlight(
            severity=_severity(after.score_pct - insights.overall.score_pct, after.games),
            text=f"After two losses in a row you score {_pct(after.score_pct)} "
            f"({after.games} games) vs {_pct(insights.overall.score_pct)} overall. "
            "Consider stopping after two straight losses.",
        )
    ]


def _sessions(insights: TimeClassInsights) -> list[Highlight]:
    return [
        Highlight(
            severity=_severity(b.summary.score_pct - insights.overall.score_pct, b.summary.games),
            text=f"Long sessions hurt: in {b.label} of a sitting you score "
            f"{_pct(b.summary.score_pct)} ({b.summary.games} games).",
        )
        for b in insights.by_session_position
        if b.label != "1st game" and _underperforms(b.summary, insights.overall, MIN_BUCKET_GAMES)
    ]


def _day_parts(insights: TimeClassInsights) -> list[Highlight]:
    return [
        Highlight(
            severity=_severity(s.score_pct - insights.overall.score_pct, s.games),
            text=f"You play worse in the {part.value}: {_pct(s.score_pct)} over {s.games} games.",
        )
        for part, s in insights.by_day_part.items()
        if _underperforms(s, insights.overall, MIN_BUCKET_GAMES)
    ]


def _clock(insights: TimeClassInsights) -> list[Highlight]:
    clock = insights.clock
    if clock is None:
        return []
    highlights = []
    trouble = clock.in_trouble
    share = 100 * trouble.games / clock.games
    if trouble.games >= MIN_GAMES and share >= TIME_TROUBLE_SHARE_PCT:
        gap = trouble.score_pct - clock.not_in_trouble.score_pct
        highlights.append(
            Highlight(
                severity=_severity(gap, trouble.games),
                text=f"You get into time trouble (under 10% of your clock) in {_pct(share)} "
                f"of games and score {_pct(trouble.score_pct)} there vs "
                f"{_pct(clock.not_in_trouble.score_pct)} otherwise.",
            )
        )
    if clock.losses >= MIN_GAMES:
        on_time = 100 * clock.losses_on_time / clock.losses
        if on_time >= TIME_LOSS_SHARE_PCT:
            highlights.append(
                Highlight(
                    severity=_severity(on_time, clock.losses_on_time) / 2,
                    text=f"{_pct(on_time)} of your losses are on time "
                    f"({clock.losses_on_time} of {clock.losses}).",
                )
            )
    return highlights


def _opponents(insights: TimeClassInsights) -> list[Highlight]:
    return [
        Highlight(
            severity=_severity(b.summary.score_pct - b.expected_score_pct, b.summary.games),
            text=f"Against {b.label} opponents you score {_pct(b.summary.score_pct)} "
            f"where rating predicts {_pct(b.expected_score_pct)} ({b.summary.games} games).",
        )
        for b in insights.by_rating_gap
        if b.summary.games >= MIN_BUCKET_GAMES
        and b.summary.score_pct <= b.expected_score_pct - NOTABLE_GAP_PCT
    ]


def _rating_trend(insights: TimeClassInsights) -> list[Highlight]:
    months = insights.rating_by_month
    if len(months) <= TREND_MONTHS:
        return []
    change = months[-1].rating - months[-1 - TREND_MONTHS].rating
    if abs(change) < NOTABLE_RATING_CHANGE:
        return []
    return [
        Highlight(
            severity=abs(change) / 10,
            text=f"Rating {change:+d} over the last {TREND_MONTHS} months "
            f"(now {months[-1].rating}).",
            strength=change > 0,
        )
    ]
