from collections.abc import Sequence
from datetime import datetime, timedelta
from itertools import groupby, takewhile

from chesscoach.domain.entities import Game, GameAnalysis
from chesscoach.domain.puzzles import Attempt, Puzzle
from chesscoach.domain.services.classification import win_pct
from chesscoach.domain.value_objects import MoveClass

MIN_WIN_PCT_FOR_PUZZLE = 15.0
REVIEW_DAYS_BY_STREAK = {1: 3, 2: 7}
MAX_REVIEW_DAYS = 30


def puzzles_from(reviews: Sequence[tuple[Game, GameAnalysis]]) -> list[Puzzle]:
    result = []
    for game, analysis in reviews:
        for move in analysis.moves:
            if (
                move.color is game.user_color
                and move.move_class in (MoveClass.MISTAKE, MoveClass.BLUNDER)
                and move.best_move_san is not None
                and win_pct(move.eval_before, game.user_color) >= MIN_WIN_PCT_FOR_PUZZLE
            ):
                result.append(
                    Puzzle(
                        id=f"{game.id}:{move.ply}",
                        game_id=game.id,
                        game_url=game.url,
                        played_at=game.played_at,
                        time_class=game.time_class,
                        opponent=game.opponent.username,
                        ply=move.ply,
                        color=game.user_color,
                        fen=move.fen_before,
                        played_san=move.san,
                        solution_san=move.best_move_san,
                        mistake=move.move_class,
                        phase=move.phase,
                        win_pct_loss=move.win_pct_loss,
                    )
                )
    return result


def due_puzzles(
    puzzles: Sequence[Puzzle], attempts: Sequence[Attempt], *, now: datetime, limit: int
) -> list[Puzzle]:
    attempts_by_id = {
        pid: sorted(group, key=lambda a: a.attempted_at)
        for pid, group in groupby(
            sorted(attempts, key=lambda a: a.puzzle_id), key=lambda a: a.puzzle_id
        )
    }

    failed: list[tuple[datetime, Puzzle]] = []
    new: list[Puzzle] = []
    due_solved: list[tuple[datetime, Puzzle]] = []

    for puzzle in puzzles:
        puzzle_attempts = attempts_by_id.get(puzzle.id, [])
        if not puzzle_attempts:
            new.append(puzzle)
        else:
            last = puzzle_attempts[-1]
            if not last.solved:
                failed.append((last.attempted_at, puzzle))
            else:
                streak = sum(1 for _ in takewhile(lambda a: a.solved, reversed(puzzle_attempts)))
                interval_days = REVIEW_DAYS_BY_STREAK.get(streak, MAX_REVIEW_DAYS)
                due_at = last.attempted_at + timedelta(days=interval_days)
                if due_at <= now:
                    due_solved.append((last.attempted_at, puzzle))

    failed.sort(reverse=True)
    new.sort(key=lambda p: -p.win_pct_loss)
    due_solved.sort()

    result = [p for _, p in failed] + new + [p for _, p in due_solved]
    return result[:limit]
