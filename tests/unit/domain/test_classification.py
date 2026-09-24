import pytest

from chesscoach.domain.services.classification import (
    assess_move,
    classify,
    game_accuracy,
    move_accuracy,
    win_pct,
)
from chesscoach.domain.value_objects import Color, Evaluation, MoveClass


def test_equal_position_is_even_for_both_sides() -> None:
    assert win_pct(Evaluation.cp(0), Color.WHITE) == 50.0
    assert win_pct(Evaluation.cp(0), Color.BLACK) == 50.0


def test_pawn_advantage_follows_lichess_curve_and_mirrors_for_black() -> None:
    assert win_pct(Evaluation.cp(100), Color.WHITE) == pytest.approx(59.1, abs=0.05)
    assert win_pct(Evaluation.cp(100), Color.BLACK) == pytest.approx(40.9, abs=0.05)


def test_forced_mate_is_certain_win_for_the_mating_side() -> None:
    assert win_pct(Evaluation.mate(3), Color.WHITE) == 100.0
    assert win_pct(Evaluation.mate(-2), Color.WHITE) == 0.0


@pytest.mark.parametrize(
    ("loss", "expected"),
    [
        (-3.0, MoveClass.GOOD),
        (4.9, MoveClass.GOOD),
        (5.0, MoveClass.INACCURACY),
        (10.0, MoveClass.MISTAKE),
        (15.0, MoveClass.BLUNDER),
    ],
)
def test_moves_are_classified_by_win_pct_loss(loss: float, expected: MoveClass) -> None:
    assert classify(loss, played_best=False) is expected


def test_engine_best_move_is_best_regardless_of_rounding_noise() -> None:
    assert classify(1.2, played_best=True) is MoveClass.BEST


def test_move_accuracy_is_full_for_no_loss_and_drops_with_loss() -> None:
    assert move_accuracy(0.0) == 100.0
    assert move_accuracy(15.0) == pytest.approx(51.5, abs=0.1)
    assert move_accuracy(100.0) == 0.0


def test_game_accuracy_blends_arithmetic_and_harmonic_means() -> None:
    assert game_accuracy([]) is None
    assert game_accuracy([100.0, 50.0]) == pytest.approx((75.0 + 66.667) / 2, abs=0.01)


def test_assess_move_measures_loss_from_the_movers_point_of_view() -> None:
    loss, move_class = assess_move(
        Color.BLACK, Evaluation.cp(0), Evaluation.cp(400), played_best=False
    )

    assert loss == pytest.approx(50.0 - win_pct(Evaluation.cp(400), Color.BLACK))
    assert move_class is MoveClass.BLUNDER
