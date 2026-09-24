"""Turn insights into ranked coaching highlights. Thresholds favour signal over noise."""

import math

from chesscoach.domain.insights import EngineInsights, Highlight, TimeClassInsights
from chesscoach.domain.services.statistics import ResultSummary

MIN_GAMES = 20
MIN_BUCKET_GAMES = 30
NOTABLE_GAP_PCT = 8.0
TIME_TROUBLE_SHARE_PCT = 20.0
TIME_LOSS_SHARE_PCT = 25.0
NOTABLE_RATING_CHANGE = 25
TREND_MONTHS = 3
MIN_PHASE_MOVES = 100
MIN_PHASES_TO_COMPARE = 2
PHASE_CONCENTRATION = 1.5
MIN_LOW_CLOCK_MOVES = 30
TIME_PRESSURE_FACTOR = 2.0
MIN_MISSED_MATES = 3
MIN_PUNISH_OPPORTUNITIES = 10
UNPUNISHED_SHARE_PCT = 30.0
MIN_WINNING_GAMES = 10
POOR_CONVERSION_PCT = 80.0
GOOD_CONVERSION_PCT = 90.0


def find_highlights(insights: TimeClassInsights) -> list[Highlight]:
    highlights = [
        *_openings(insights),
        *_tilt(insights),
        *_sessions(insights),
        *_day_parts(insights),
        *_clock(insights),
        *_opponents(insights),
        *_rating_trend(insights),
        *_engine(insights.engine),
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
    if not months:
        return []
    latest = months[-1]
    cutoff = latest.year * 12 + latest.month - 1 - TREND_MONTHS
    earlier = [m for m in months if m.year * 12 + m.month - 1 <= cutoff]
    if not earlier:
        return []
    change = latest.rating - earlier[-1].rating
    if abs(change) < NOTABLE_RATING_CHANGE:
        return []
    return [
        Highlight(
            severity=abs(change) / 10,
            text=f"Rating {change:+d} over the last {TREND_MONTHS} months (now {latest.rating}).",
            strength=change > 0,
        )
    ]


def _engine(engine: EngineInsights | None) -> list[Highlight]:
    if engine is None:
        return []
    return [
        *_error_phase(engine),
        *_time_pressure(engine),
        *_missed_mates(engine),
        *_unpunished(engine),
        *_conversion(engine),
    ]


def _error_phase(engine: EngineInsights) -> list[Highlight]:
    phases = [p for p in engine.by_phase if p.moves >= MIN_PHASE_MOVES]
    if len(phases) < MIN_PHASES_TO_COMPARE:
        return []
    worst = max(phases, key=lambda p: p.serious_per_100)
    others = [p.serious_per_100 for p in phases if p is not worst]
    baseline = sum(others) / len(others)
    if worst.serious_per_100 < PHASE_CONCENTRATION * max(baseline, 0.1):
        return []
    return [
        Highlight(
            severity=_severity(worst.serious_per_100 - baseline, worst.moves) / 2,
            text=f"Your serious errors concentrate in the {worst.phase.value}: "
            f"{worst.serious_per_100:.1f} per 100 moves vs {baseline:.1f} in other phases.",
        )
    ]


def _time_pressure(engine: EngineInsights) -> list[Highlight]:
    pressure = engine.time_pressure
    if pressure is None or pressure.low_moves < MIN_LOW_CLOCK_MOVES:
        return []
    if pressure.low_rate < TIME_PRESSURE_FACTOR * max(pressure.normal_rate, 0.1):
        return []
    return [
        Highlight(
            severity=_severity(pressure.low_rate - pressure.normal_rate, pressure.low_moves),
            text=f"Under 10% of your clock, {_pct(pressure.low_rate)} of your moves are "
            f"mistakes or blunders vs {_pct(pressure.normal_rate)} otherwise.",
        )
    ]


def _missed_mates(engine: EngineInsights) -> list[Highlight]:
    missed = len(engine.missed_mates)
    if missed < MIN_MISSED_MATES:
        return []
    return [
        Highlight(
            severity=missed,
            text=f"You missed {missed} forced mates in {engine.games} analyzed games. "
            "Look for checks and captures first when you are attacking.",
        )
    ]


def _unpunished(engine: EngineInsights) -> list[Highlight]:
    chances = engine.punish_opportunities
    if chances < MIN_PUNISH_OPPORTUNITIES:
        return []
    share = 100 * len(engine.unpunished) / chances
    if share < UNPUNISHED_SHARE_PCT:
        return []
    return [
        Highlight(
            severity=_severity(share, chances),
            text=f"When your opponent blunders, {_pct(share)} of your replies are mistakes "
            f"or blunders ({len(engine.unpunished)} of {chances}). Ask what their last move "
            "allowed.",
        )
    ]


def _conversion(engine: EngineInsights) -> list[Highlight]:
    conversion = engine.conversion
    if conversion.winning_games < MIN_WINNING_GAMES:
        return []
    detail = f"{_pct(conversion.rate)} of clearly winning positions "
    detail += f"({conversion.converted} of {conversion.winning_games})"
    if conversion.rate < POOR_CONVERSION_PCT:
        return [
            Highlight(
                severity=_severity(GOOD_CONVERSION_PCT - conversion.rate, conversion.winning_games),
                text=f"You only convert {detail}. Simplify and trade when ahead.",
            )
        ]
    if conversion.rate >= GOOD_CONVERSION_PCT:
        return [Highlight(severity=1.0, text=f"You convert {detail}.", strength=True)]
    return []
