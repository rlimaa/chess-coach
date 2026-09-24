from pathlib import Path

from chesscoach.adapters.persistence.sqlite.analysis_repository import SqliteAnalysisRepository
from chesscoach.adapters.persistence.sqlite.database import SqliteDatabase
from chesscoach.adapters.persistence.sqlite.evaluation_cache import SqliteEvaluationCache
from chesscoach.adapters.persistence.sqlite.game_repository import SqliteGameRepository
from chesscoach.application.dto import EngineLine
from chesscoach.domain.entities import GameAnalysis, MoveAnalysis
from chesscoach.domain.value_objects import Color, Evaluation, MoveClass, Phase
from tests.builders import make_game

ANALYSIS = GameAnalysis(
    game_id="g1",
    depth=14,
    moves=(
        MoveAnalysis(
            ply=0,
            color=Color.WHITE,
            san="e4",
            fen_before="start",
            phase=Phase.OPENING,
            eval_before=Evaluation.cp(30),
            eval_after=Evaluation.cp(35),
            best_move_san="e4",
            win_pct_loss=-0.4,
            move_class=MoveClass.BEST,
            clock_seconds=179.9,
        ),
        MoveAnalysis(
            ply=1,
            color=Color.BLACK,
            san="Qh4",
            fen_before="after e4",
            phase=Phase.ENDGAME,
            eval_before=Evaluation.cp(35),
            eval_after=Evaluation.mate(2),
            best_move_san=None,
            win_pct_loss=48.2,
            move_class=MoveClass.BLUNDER,
            clock_seconds=None,
        ),
    ),
)


def _db(tmp_path: Path) -> SqliteDatabase:
    return SqliteDatabase(tmp_path / "coach.db")


def test_analysis_round_trips_with_every_move(tmp_path: Path) -> None:
    repo = SqliteAnalysisRepository(_db(tmp_path))

    repo.save(ANALYSIS)

    assert repo.get("g1") == ANALYSIS
    assert repo.get("missing") is None
    assert repo.analyzed_ids() == {"g1"}


def test_saving_again_replaces_the_previous_analysis(tmp_path: Path) -> None:
    repo = SqliteAnalysisRepository(_db(tmp_path))
    repo.save(ANALYSIS)
    deeper = GameAnalysis(game_id="g1", depth=20, moves=ANALYSIS.moves[:1])

    repo.save(deeper)

    assert repo.get("g1") == deeper


def test_evaluation_cache_is_keyed_by_position_and_depth(tmp_path: Path) -> None:
    cache = SqliteEvaluationCache(_db(tmp_path))
    line = EngineLine(Evaluation.mate(-3), None, None)

    cache.put("fen", 12, line)

    assert cache.get("fen", 12) == line
    assert cache.get("fen", 16) is None


def test_games_can_be_found_by_id_url_or_url_number(tmp_path: Path) -> None:
    repo = SqliteGameRepository(_db(tmp_path))
    game = make_game(id="uuid-1", url="https://www.chess.com/game/live/12345")
    repo.add([game])

    assert repo.find("uuid-1") == game
    assert repo.find("https://www.chess.com/game/live/12345") == game
    assert repo.find("12345") == game
    assert repo.find("999") is None
