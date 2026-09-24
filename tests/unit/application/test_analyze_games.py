from datetime import UTC, datetime

from chesscoach.application.dto import EngineLine, Ply, ReplayedGame
from chesscoach.application.use_cases.analyze_games import AnalyzeGames
from chesscoach.domain.value_objects import Color, Evaluation, MoveClass, Phase, TimeClass
from tests.builders import make_game
from tests.fakes import FakeEngine, FakeReplayer, InMemoryAnalysisRepository, InMemoryGameRepository

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
AFTER_E4 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
AFTER_F6 = "rnbqkbnr/ppppp1pp/5p2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"

REPLAY = ReplayedGame(
    plies=(
        Ply(0, Color.WHITE, "e4", "e2e4", START, 180.0),
        Ply(1, Color.BLACK, "f6", "f7f6", AFTER_E4, 178.5),
    ),
    final_fen=AFTER_F6,
)
LINES = {
    START: EngineLine(Evaluation.cp(30), "e2e4", "e4"),
    AFTER_E4: EngineLine(Evaluation.cp(35), "e7e5", "e5"),
    AFTER_F6: EngineLine(Evaluation.cp(250), "d2d4", "d4"),
}


def _setup(*game_ids: str) -> tuple[AnalyzeGames, InMemoryAnalysisRepository, FakeEngine]:
    games = InMemoryGameRepository()
    games.add(
        make_game(id=gid, pgn="pgn", played_at=datetime(2026, 9, day, tzinfo=UTC))
        for day, gid in enumerate(game_ids, start=1)
    )
    analyses, engine = InMemoryAnalysisRepository(), FakeEngine(LINES)
    return AnalyzeGames(games, analyses, FakeReplayer({"pgn": REPLAY}), engine), analyses, engine


def test_analysis_judges_every_move_against_the_engine() -> None:
    use_case, analyses, _ = _setup("g1")

    use_case.execute("me", limit=5, depth=14)

    analysis = analyses.get("g1")
    assert analysis is not None
    assert analysis.depth == 14
    e4, f6 = analysis.moves
    assert e4.move_class is MoveClass.BEST
    assert (e4.eval_before, e4.eval_after) == (Evaluation.cp(30), Evaluation.cp(35))
    assert f6.color is Color.BLACK
    assert f6.best_move_san == "e5"
    assert f6.move_class is MoveClass.BLUNDER
    assert f6.phase is Phase.OPENING
    assert f6.clock_seconds == 178.5


def test_each_position_is_evaluated_once_at_requested_depth() -> None:
    use_case, _, engine = _setup("g1")

    use_case.execute("me", limit=1, depth=10)

    assert engine.calls == [(START, 10), (AFTER_E4, 10), (AFTER_F6, 10)]


def test_most_recent_unanalyzed_games_go_first_and_are_not_redone() -> None:
    use_case, analyses, _ = _setup("old", "mid", "new")

    first = use_case.execute("me", limit=2, depth=8)
    second = use_case.execute("me", limit=2, depth=8)

    assert (first.analyzed, first.still_pending) == (2, 1)
    assert (second.analyzed, second.still_pending) == (1, 0)
    assert analyses.analyzed_ids() == {"old", "mid", "new"}


def test_progress_is_reported_per_game() -> None:
    use_case, _, _ = _setup("a", "b")
    seen: list[tuple[str, int, int]] = []

    use_case.execute("me", limit=5, depth=8, on_progress=lambda g, i, n: seen.append((g.id, i, n)))

    assert seen == [("b", 1, 2), ("a", 2, 2)]


def test_analysis_can_be_limited_to_one_time_class() -> None:
    games = InMemoryGameRepository()
    games.add(
        [
            make_game(id="blitz", pgn="pgn", time_class=TimeClass.BLITZ),
            make_game(id="rapid", pgn="pgn", time_class=TimeClass.RAPID),
        ]
    )
    analyses = InMemoryAnalysisRepository()
    use_case = AnalyzeGames(games, analyses, FakeReplayer({"pgn": REPLAY}), FakeEngine(LINES))

    report = use_case.execute("me", limit=5, depth=8, time_class=TimeClass.RAPID)

    assert analyses.analyzed_ids() == {"rapid"}
    assert report.still_pending == 0
