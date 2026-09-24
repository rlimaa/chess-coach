from chesscoach.domain.entities import GameAnalysis, MoveAnalysis
from chesscoach.domain.value_objects import Color, Evaluation, MoveClass, Phase


def _move(ply: int, color: Color, loss: float, move_class: MoveClass) -> MoveAnalysis:
    return MoveAnalysis(
        ply=ply,
        color=color,
        san="e4",
        fen_before="fen",
        phase=Phase.OPENING,
        eval_before=Evaluation.cp(0),
        eval_after=Evaluation.cp(0),
        best_move_san="e4",
        win_pct_loss=loss,
        move_class=move_class,
        clock_seconds=None,
    )


ANALYSIS = GameAnalysis(
    game_id="g",
    depth=12,
    moves=(
        _move(0, Color.WHITE, 0.0, MoveClass.BEST),
        _move(1, Color.BLACK, 20.0, MoveClass.BLUNDER),
        _move(2, Color.WHITE, 0.0, MoveClass.BEST),
        _move(3, Color.BLACK, 6.0, MoveClass.INACCURACY),
    ),
)


def test_accuracy_is_computed_per_color() -> None:
    white = ANALYSIS.accuracy(Color.WHITE)
    black = ANALYSIS.accuracy(Color.BLACK)

    assert white == 100.0
    assert black is not None
    assert black < 70


def test_counts_move_classes_per_color() -> None:
    assert ANALYSIS.count(Color.BLACK, MoveClass.BLUNDER) == 1
    assert ANALYSIS.count(Color.WHITE, MoveClass.BLUNDER) == 0
