from chesscoach.domain.services.statistics import summarize
from chesscoach.domain.value_objects import Outcome
from tests.builders import make_game


def test_summary_counts_outcomes_and_scores_draws_as_half() -> None:
    games = [make_game(outcome=o) for o in (Outcome.WIN, Outcome.WIN, Outcome.DRAW, Outcome.LOSS)]

    summary = summarize(games)

    assert (summary.games, summary.wins, summary.draws, summary.losses) == (4, 2, 1, 1)
    assert summary.score_pct == 62.5


def test_summary_of_no_games_has_zero_score() -> None:
    summary = summarize([])

    assert summary.games == 0
    assert summary.score_pct == 0.0
