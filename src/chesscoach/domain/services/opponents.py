from collections.abc import Iterable
from itertools import pairwise
from statistics import fmean

from chesscoach.domain.entities import Game
from chesscoach.domain.insights import RatingGapBucket
from chesscoach.domain.services.statistics import summarize

# (label, smallest gap) from strongest opponents down; gap = opponent rating - user rating.
_BUCKETS = (
    ("much stronger (+100)", 100),
    ("stronger (+25..+99)", 25),
    ("similar (±24)", -24),
    ("weaker (-25..-99)", -99),
    ("much weaker (-100)", None),
)


def _pre_game_gaps(games: Iterable[Game]) -> list[tuple[Game, int]]:
    """chess.com reports ratings after the game, which biases gaps towards the result.

    Undo it: the user's pre-game rating is their rating after the previous game, and the
    opponent's rating moved by about the same amount in the other direction.
    """
    chronological = sorted(games, key=lambda g: g.played_at)
    gaps = [(chronological[0], _post_game_gap(chronological[0]))] if chronological else []
    for previous, game in pairwise(chronological):
        change = game.user.rating - previous.user.rating
        gaps.append((game, _post_game_gap(game) + 2 * change))
    return gaps


def _post_game_gap(game: Game) -> int:
    return game.opponent.rating - game.user.rating


def _bucket(gap: int) -> str:
    return next(label for label, floor in _BUCKETS if floor is None or gap >= floor)


def _expected_score_pct(gap: int) -> float:
    return 100 / (1 + 10 ** (gap / 400))


def by_rating_gap(games: Iterable[Game]) -> list[RatingGapBucket]:
    gaps = _pre_game_gaps(games)
    buckets = []
    for label, _ in _BUCKETS:
        members = [(game, gap) for game, gap in gaps if _bucket(gap) == label]
        expected = fmean(_expected_score_pct(gap) for _, gap in members) if members else 0.0
        buckets.append(RatingGapBucket(label, summarize(g for g, _ in members), expected))
    return buckets
