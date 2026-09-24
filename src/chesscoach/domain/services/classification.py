"""Move judgement and accuracy, following Lichess' published formulas."""

import math
from collections.abc import Sequence
from statistics import fmean, harmonic_mean

from chesscoach.domain.value_objects import Color, Evaluation, MoveClass

_WIN_PCT_SLOPE = 0.00368208
_INACCURACY, _MISTAKE, _BLUNDER = 5.0, 10.0, 15.0


def win_pct(evaluation: Evaluation, color: Color) -> float:
    if evaluation.mate_in is not None:
        white = 100.0 if evaluation.mate_in > 0 else 0.0
    else:
        assert evaluation.centipawns is not None
        white = 50 + 50 * (2 / (1 + math.exp(-_WIN_PCT_SLOPE * evaluation.centipawns)) - 1)
    return white if color is Color.WHITE else 100.0 - white


def classify(win_pct_loss: float, *, played_best: bool) -> MoveClass:
    if played_best:
        return MoveClass.BEST
    if win_pct_loss >= _BLUNDER:
        return MoveClass.BLUNDER
    if win_pct_loss >= _MISTAKE:
        return MoveClass.MISTAKE
    if win_pct_loss >= _INACCURACY:
        return MoveClass.INACCURACY
    return MoveClass.GOOD


def move_accuracy(win_pct_loss: float) -> float:
    raw = 103.1668 * math.exp(-0.04354 * max(win_pct_loss, 0.0)) - 3.1669 + 1  # +1: uncertainty
    return min(max(raw, 0.0), 100.0)


def game_accuracy(move_accuracies: Sequence[float]) -> float | None:
    if not move_accuracies:
        return None
    return (fmean(move_accuracies) + harmonic_mean(move_accuracies)) / 2


def assess_move(
    mover: Color, before: Evaluation, after: Evaluation, *, played_best: bool
) -> tuple[float, MoveClass]:
    loss = win_pct(before, mover) - win_pct(after, mover)
    return loss, classify(loss, played_best=played_best)
