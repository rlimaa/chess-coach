"""Composition root: the only place that builds concrete adapters from settings."""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from functools import cached_property
from importlib.metadata import version
from pathlib import Path

from chesscoach.adapters.chess_rules.board_rules import PythonChessRules
from chesscoach.adapters.chess_rules.clock_reader import PgnClockReader
from chesscoach.adapters.chess_rules.pgn_replayer import PgnReplayer
from chesscoach.adapters.chesscom.client import ChessComClient
from chesscoach.adapters.coaching.repertoire_file import JsonRepertoireFile
from chesscoach.adapters.coaching.training_plan_file import MarkdownTrainingPlanFile
from chesscoach.adapters.engine.caching import CachingEngine
from chesscoach.adapters.engine.diagnostics import EngineProbe, probe_engine
from chesscoach.adapters.engine.stockfish_engine import StockfishEngine
from chesscoach.adapters.locking.directory_lock import DirectoryLock
from chesscoach.adapters.persistence.sqlite.analysis_repository import SqliteAnalysisRepository
from chesscoach.adapters.persistence.sqlite.database import SqliteDatabase
from chesscoach.adapters.persistence.sqlite.evaluation_cache import SqliteEvaluationCache
from chesscoach.adapters.persistence.sqlite.game_repository import SqliteGameRepository
from chesscoach.adapters.persistence.sqlite.puzzle_attempts import SqlitePuzzleAttempts
from chesscoach.adapters.persistence.sqlite.response_cache import SqliteResponseCache
from chesscoach.adapters.persistence.sqlite.sync_state import SqliteSyncState
from chesscoach.adapters.reporting.markdown_report_writer import MarkdownReportWriter
from chesscoach.application.dto import LineSearch
from chesscoach.application.use_cases.analyze_games import AnalyzeGames
from chesscoach.application.use_cases.build_insights import BuildInsights
from chesscoach.application.use_cases.compare_progress import CompareProgress
from chesscoach.application.use_cases.generate_report import GenerateReport
from chesscoach.application.use_cases.get_stats import GetStats
from chesscoach.application.use_cases.puzzles import (
    ExplainPuzzle,
    FindPuzzle,
    NextPuzzles,
    SolvePuzzle,
)
from chesscoach.application.use_cases.repertoire import GetRepertoire
from chesscoach.application.use_cases.review_game import ReviewGame
from chesscoach.application.use_cases.show_games import RecentGames, ShowGame
from chesscoach.application.use_cases.sync_games import SyncGames
from chesscoach.application.use_cases.training_plan import GetTrainingPlan
from chesscoach.config import Settings

ENGINE_CHECK_DEPTH = 12
EXPLANATION_PLIES = 8
# A lock older than this belongs to a run that crashed; the longest real run takes a few hours.
ANALYSIS_LOCK_MAX_AGE = timedelta(hours=12)


class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @cached_property
    def _database(self) -> SqliteDatabase:
        return SqliteDatabase(self.settings.db_path)

    def probe_engine(self) -> EngineProbe:
        return probe_engine(self.settings.engine.path, depth=ENGINE_CHECK_DEPTH)

    def sync_games(self) -> SyncGames:
        return SyncGames(
            source=self._chesscom(),
            games=SqliteGameRepository(self._database),
            sync_state=SqliteSyncState(self._database),
        )

    def get_stats(self) -> GetStats:
        return GetStats(SqliteGameRepository(self._database))

    @contextmanager
    def analysis_session(self) -> Iterator[AnalyzeGames]:
        engine = self.settings.engine
        with StockfishEngine(engine.path, threads=engine.threads, hash_mb=engine.hash_mb) as sf:
            yield AnalyzeGames(
                games=SqliteGameRepository(self._database),
                analyses=SqliteAnalysisRepository(self._database),
                replayer=PgnReplayer(),
                engine=CachingEngine(sf, SqliteEvaluationCache(self._database)),
            )

    def review_game(self) -> ReviewGame:
        return ReviewGame(
            SqliteGameRepository(self._database), SqliteAnalysisRepository(self._database)
        )

    def generate_report(self) -> GenerateReport:
        return GenerateReport(
            games=SqliteGameRepository(self._database),
            analyses=SqliteAnalysisRepository(self._database),
            clocks=PgnClockReader(),
            writer=MarkdownReportWriter(self.settings.reports_dir),
            timezone=self.settings.timezone,
        )

    def next_puzzles(self) -> NextPuzzles:
        return NextPuzzles(
            games=SqliteGameRepository(self._database),
            analyses=SqliteAnalysisRepository(self._database),
            attempts=SqlitePuzzleAttempts(self._database),
            clock=_now,
        )

    def solve_puzzle(self) -> SolvePuzzle:
        return SolvePuzzle(PythonChessRules(), SqlitePuzzleAttempts(self._database), _now)

    @contextmanager
    def puzzle_explainer(self) -> Iterator[ExplainPuzzle]:
        engine = self.settings.engine
        with StockfishEngine(engine.path, threads=engine.threads, hash_mb=engine.hash_mb) as sf:
            yield ExplainPuzzle(
                find=self.find_puzzle(),
                attempts=SqlitePuzzleAttempts(self._database),
                rules=PythonChessRules(),
                engine=sf,
                search=LineSearch(engine.explain_depth, EXPLANATION_PLIES),
            )

    def chess_rules(self) -> PythonChessRules:
        return PythonChessRules()

    def compare_progress(self) -> CompareProgress:
        return CompareProgress(
            games=SqliteGameRepository(self._database),
            analyses=SqliteAnalysisRepository(self._database),
            clocks=PgnClockReader(),
            clock=_now,
        )

    def build_insights(self) -> BuildInsights:
        return BuildInsights(
            games=SqliteGameRepository(self._database),
            analyses=SqliteAnalysisRepository(self._database),
            clocks=PgnClockReader(),
            timezone=self.settings.timezone,
        )

    def recent_games(self) -> RecentGames:
        return RecentGames(
            games=SqliteGameRepository(self._database),
            analyses=SqliteAnalysisRepository(self._database),
        )

    def show_game(self) -> ShowGame:
        return ShowGame(
            games=SqliteGameRepository(self._database),
            analyses=SqliteAnalysisRepository(self._database),
            replayer=PgnReplayer(),
        )

    def find_puzzle(self) -> FindPuzzle:
        return FindPuzzle(
            games=SqliteGameRepository(self._database),
            analyses=SqliteAnalysisRepository(self._database),
        )

    def analysis_lock(self) -> DirectoryLock:
        return DirectoryLock(self.data_dir / ".analysis.lock", max_age=ANALYSIS_LOCK_MAX_AGE)

    @property
    def data_dir(self) -> Path:
        return self.settings.db_path.parent

    def get_repertoire(self) -> GetRepertoire:
        return GetRepertoire(JsonRepertoireFile(self.settings.repertoire_path), PythonChessRules())

    def get_training_plan(self) -> GetTrainingPlan:
        return GetTrainingPlan(MarkdownTrainingPlanFile(self.settings.training_plan_path))

    def _chesscom(self) -> ChessComClient:
        return ChessComClient(
            user_agent=self._user_agent(), cache=SqliteResponseCache(self._database)
        )

    def _user_agent(self) -> str:
        agent = f"chesscoach/{version('chess-coach')}"
        if self.settings.contact_email:
            agent += f" (contact: {self.settings.contact_email})"
        return agent


def _now() -> datetime:
    return datetime.now(UTC)
