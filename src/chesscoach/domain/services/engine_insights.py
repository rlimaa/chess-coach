from collections.abc import Iterator, Sequence
from itertools import pairwise
from statistics import fmean

from chesscoach.domain.entities import Game, GameAnalysis, MoveAnalysis
from chesscoach.domain.insights import (
    Conversion,
    EngineInsights,
    MomentRef,
    PhaseErrors,
    TimePressureErrors,
)
from chesscoach.domain.services.classification import win_pct
from chesscoach.domain.value_objects import Color, Evaluation, MoveClass, Outcome, Phase

Review = tuple[Game, GameAnalysis]

WINNING_WIN_PCT = 85.0
LOW_CLOCK_SHARE = 0.10
SERIOUS = frozenset({MoveClass.MISTAKE, MoveClass.BLUNDER})


def engine_insights(reviews: Sequence[Review]) -> EngineInsights | None:
    if not reviews:
        return None
    opportunities, unpunished = _punishing(reviews)
    return EngineInsights(
        games=len(reviews),
        accuracy=_mean_accuracy(reviews, opponent=False),
        opponent_accuracy=_mean_accuracy(reviews, opponent=True),
        by_phase=tuple(_phase_errors(phase, reviews) for phase in Phase),
        time_pressure=_time_pressure(reviews),
        missed_mates=tuple(
            _moment(game, move)
            for game, move in _user_moves(reviews)
            if _mates_for(move.eval_before, game.user_color)
            and not _mates_for(move.eval_after, game.user_color)
            and move.move_class in SERIOUS
        ),
        punish_opportunities=opportunities,
        unpunished=unpunished,
        conversion=_conversion(reviews),
    )


def _user_moves(reviews: Sequence[Review]) -> Iterator[tuple[Game, MoveAnalysis]]:
    for game, analysis in reviews:
        for move in analysis.moves:
            if move.color is game.user_color:
                yield game, move


def _moment(game: Game, move: MoveAnalysis) -> MomentRef:
    return MomentRef(game.url, move.ply, move.san, move.best_move_san)


def _mean_accuracy(reviews: Sequence[Review], *, opponent: bool) -> float | None:
    values = [
        accuracy
        for game, analysis in reviews
        if (accuracy := analysis.accuracy(game.opponent_color if opponent else game.user_color))
        is not None
    ]
    return fmean(values) if values else None


def _phase_errors(phase: Phase, reviews: Sequence[Review]) -> PhaseErrors:
    moves = [move for _, move in _user_moves(reviews) if move.phase is phase]
    classes = [move.move_class for move in moves]
    return PhaseErrors(
        phase=phase,
        moves=len(moves),
        avg_win_pct_loss=fmean(max(m.win_pct_loss, 0.0) for m in moves) if moves else 0.0,
        inaccuracies=classes.count(MoveClass.INACCURACY),
        mistakes=classes.count(MoveClass.MISTAKE),
        blunders=classes.count(MoveClass.BLUNDER),
    )


def _time_pressure(reviews: Sequence[Review]) -> TimePressureErrors | None:
    low: list[bool] = []
    normal: list[bool] = []
    for game, move in _user_moves(reviews):
        if game.time_control.is_correspondence or move.clock_seconds is None:
            continue
        is_low = move.clock_seconds < LOW_CLOCK_SHARE * game.time_control.base_seconds
        (low if is_low else normal).append(move.move_class in SERIOUS)
    if not low and not normal:
        return None
    return TimePressureErrors(len(low), sum(low), len(normal), sum(normal))


def _mates_for(evaluation: Evaluation, color: Color) -> bool:
    mate = evaluation.mate_in
    return mate is not None and (mate > 0) == (color is Color.WHITE)


def _punishing(reviews: Sequence[Review]) -> tuple[int, tuple[MomentRef, ...]]:
    replies = [
        (game, reply)
        for game, analysis in reviews
        for blunder, reply in pairwise(analysis.moves)
        if blunder.color is game.opponent_color
        and blunder.move_class is MoveClass.BLUNDER
        and reply.color is game.user_color
    ]
    unpunished = tuple(
        _moment(game, reply) for game, reply in replies if reply.move_class in SERIOUS
    )
    return len(replies), unpunished


def _conversion(reviews: Sequence[Review]) -> Conversion:
    winning = 0
    thrown: list[MomentRef] = []
    for game, analysis in reviews:
        first_winning = next(
            (
                move
                for move in analysis.moves
                if move.color is game.user_color
                and win_pct(move.eval_before, game.user_color) >= WINNING_WIN_PCT
            ),
            None,
        )
        if first_winning is None:
            continue
        winning += 1
        if game.outcome is not Outcome.WIN:
            thrown.append(_moment(game, first_winning))
    return Conversion(winning_games=winning, converted=winning - len(thrown), thrown=tuple(thrown))
