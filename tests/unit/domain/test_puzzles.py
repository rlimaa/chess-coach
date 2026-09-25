from datetime import UTC, datetime, timedelta

from chesscoach.domain.entities import PlayerSide
from chesscoach.domain.puzzles import Attempt, Puzzle
from chesscoach.domain.services.puzzles import due_puzzles, puzzles_from
from chesscoach.domain.value_objects import Color, Evaluation, MoveClass, Phase, TimeClass
from tests.builders import make_analysis, make_game, make_move

NOW = datetime(2026, 9, 24, 12, tzinfo=UTC)


def test_puzzles_come_from_the_users_mistakes_and_blunders_with_a_known_best_move() -> None:
    game = make_game(
        id="g1",
        url="https://chess.com/g1",
        user_color=Color.WHITE,
        black=PlayerSide("rival", 1500),
        time_class=TimeClass.BLITZ,
    )
    analysis = make_analysis(
        game,
        make_move(color=Color.WHITE, move_class=MoveClass.INACCURACY, win_pct_loss=6.0),
        make_move(color=Color.BLACK, move_class=MoveClass.BLUNDER, win_pct_loss=30.0),
        make_move(
            color=Color.WHITE,
            fen_before="fen-before",
            san="Rg6+",
            best_move_san="Nxf4",
            move_class=MoveClass.BLUNDER,
            win_pct_loss=40.0,
            phase=Phase.ENDGAME,
        ),
        make_move(color=Color.WHITE, move_class=MoveClass.MISTAKE, best_move_san=None),
    )

    (puzzle,) = puzzles_from([(game, analysis)])

    assert puzzle.id == "g1:2"
    assert (puzzle.fen, puzzle.played_san, puzzle.solution_san) == ("fen-before", "Rg6+", "Nxf4")
    assert (puzzle.mistake, puzzle.phase, puzzle.win_pct_loss) == (
        MoveClass.BLUNDER,
        Phase.ENDGAME,
        40.0,
    )
    assert (puzzle.opponent, puzzle.time_class, puzzle.game_url) == (
        "rival",
        TimeClass.BLITZ,
        "https://chess.com/g1",
    )
    assert puzzle.color is Color.WHITE


def test_positions_that_were_already_lost_are_not_puzzles() -> None:
    game = make_game(user_color=Color.WHITE)
    analysis = make_analysis(
        game,
        make_move(
            color=Color.WHITE,
            eval_before=Evaluation.cp(-900),
            move_class=MoveClass.BLUNDER,
            win_pct_loss=15.0,
        ),
    )

    assert puzzles_from([(game, analysis)]) == []


def _puzzle(pid: str, loss: float = 20.0) -> Puzzle:
    return Puzzle(
        id=pid,
        game_id=pid,
        game_url="u",
        played_at=NOW,
        time_class=TimeClass.BLITZ,
        opponent="x",
        ply=0,
        color=Color.WHITE,
        fen="f",
        played_san="a3",
        solution_san="e4",
        mistake=MoveClass.BLUNDER,
        phase=Phase.MIDDLEGAME,
        win_pct_loss=loss,
    )


def _ago(days: float, solved: bool, pid: str) -> Attempt:
    return Attempt(pid, NOW - timedelta(days=days), solved)


def test_failed_puzzles_come_first_then_new_ones_biggest_blunder_first() -> None:
    puzzles = [_puzzle("new-small", 12.0), _puzzle("new-big", 50.0), _puzzle("failed")]
    attempts = [_ago(3, False, "failed")]

    due = due_puzzles(puzzles, attempts, now=NOW, limit=10)

    assert [p.id for p in due] == ["failed", "new-big", "new-small"]


def test_solved_puzzles_rest_for_growing_intervals() -> None:
    puzzles = [_puzzle("once"), _puzzle("once-ready"), _puzzle("twice"), _puzzle("thrice")]
    attempts = [
        _ago(2, True, "once"),
        _ago(4, True, "once-ready"),
        _ago(10, True, "twice"),
        _ago(5, True, "twice"),
        _ago(60, True, "thrice"),
        _ago(40, True, "thrice"),
        _ago(20, True, "thrice"),
    ]

    due = due_puzzles(puzzles, attempts, now=NOW, limit=10)

    assert [p.id for p in due] == ["once-ready"]


def test_a_failure_resets_the_interval_and_limit_caps_the_session() -> None:
    puzzles = [_puzzle("relapsed"), _puzzle("a"), _puzzle("b")]
    attempts = [
        _ago(30, True, "relapsed"),
        _ago(20, True, "relapsed"),
        _ago(2.5, False, "relapsed"),
    ]

    due = due_puzzles(puzzles, attempts, now=NOW, limit=2)

    assert [p.id for p in due] == ["relapsed", "a"]


def test_only_the_latest_run_of_successes_counts_towards_the_interval() -> None:
    attempts = [_ago(20, True, "p"), _ago(10, False, "p"), _ago(4, True, "p")]

    assert [p.id for p in due_puzzles([_puzzle("p")], attempts, now=NOW, limit=5)] == ["p"]


def test_a_missed_puzzle_rests_two_days_so_it_never_repeats_the_next_day() -> None:
    puzzles = [_puzzle("yesterday"), _puzzle("two-days-ago")]
    attempts = [_ago(1, False, "yesterday"), _ago(2, False, "two-days-ago")]

    due = due_puzzles(puzzles, attempts, now=NOW, limit=10)

    assert [p.id for p in due] == ["two-days-ago"]
