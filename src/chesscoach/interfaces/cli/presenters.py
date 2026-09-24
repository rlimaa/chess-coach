from rich.console import Console
from rich.table import Table

from chesscoach.adapters.engine.diagnostics import EngineProbe
from chesscoach.application.dto import (
    AnalyzeReport,
    GameReview,
    PlayerStats,
    SyncReport,
    WrittenReport,
)
from chesscoach.domain.entities import MoveAnalysis
from chesscoach.domain.services.statistics import ResultSummary
from chesscoach.domain.value_objects import Evaluation, MoveClass

_KEY_MOMENTS = (MoveClass.INACCURACY, MoveClass.MISTAKE, MoveClass.BLUNDER)
_CLASS_STYLE = {
    MoveClass.INACCURACY: "yellow",
    MoveClass.MISTAKE: "dark_orange",
    MoveClass.BLUNDER: "bold red",
}


def show_engine_probe(console: Console, probe: EngineProbe) -> None:
    table = Table(title="Engine check", show_header=False)
    table.add_row("Engine", probe.name)
    table.add_row("Depth", str(probe.depth))
    table.add_row("Best move (start position)", probe.best_move)
    score = "mate" if probe.score_cp is None else f"{probe.score_cp / 100:+.2f}"
    table.add_row("Evaluation (white)", score)
    console.print(table)


def show_error(console: Console, message: str) -> None:
    console.print(f"[bold red]Error:[/] {message}")


def show_sync_report(console: Console, username: str, report: SyncReport) -> None:
    console.print(
        f"Synced {username}: {report.games_added} new games "
        f"({report.games_fetched} fetched from {report.months_fetched} month(s))."
    )


def _wdl(summary: ResultSummary) -> list[str]:
    return [
        str(summary.games),
        f"{summary.wins}/{summary.draws}/{summary.losses}",
        f"{summary.score_pct:.1f}%",
    ]


def show_stats(console: Console, stats: PlayerStats) -> None:
    if stats.overall.games == 0:
        console.print(f"No games stored for {stats.username}. Run `coach sync` first.")
        return

    console.print(
        f"[bold]{stats.username}[/]: {stats.overall.games} games, "
        f"score {stats.overall.score_pct:.1f}%"
    )

    time_classes = Table(title="By time class")
    for column in ("Time class", "Games", "W/D/L", "Score", "Rating", "Peak"):
        time_classes.add_column(column)
    for time_class, tc_stats in sorted(stats.by_time_class.items()):
        time_classes.add_row(
            time_class.value,
            *_wdl(tc_stats.summary),
            str(tc_stats.current_rating),
            str(tc_stats.peak_rating),
        )
    console.print(time_classes)

    colors = Table(title="By color")
    for column in ("Color", "Games", "W/D/L", "Score"):
        colors.add_column(column)
    for color, summary in stats.by_color.items():
        colors.add_row(color.value, *_wdl(summary))
    console.print(colors)

    openings = Table(title="Most played openings")
    for column in ("Opening", "Games", "W/D/L", "Score"):
        openings.add_column(column)
    for opening in stats.openings:
        openings.add_row(opening.name, *_wdl(opening.summary))
    console.print(openings)


def show_analyze_report(console: Console, report: AnalyzeReport, depth: int) -> None:
    console.print(
        f"Analyzed {report.analyzed} game(s) at depth {depth}; "
        f"{report.still_pending} still pending."
    )


def show_game_review(console: Console, review: GameReview) -> None:
    game, analysis = review.game, review.analysis
    console.print(
        f"[bold]{game.white.username}[/] ({game.white.rating}) vs "
        f"[bold]{game.black.username}[/] ({game.black.rating}) · {game.time_class.value} "
        f"{game.time_control} · {game.played_at:%Y-%m-%d}"
    )
    console.print(
        f"You played {game.user_color.value}: {game.outcome.value} by {game.termination} "
        f"· engine depth {analysis.depth} · {game.url}"
    )

    summary = Table(title="Accuracy")
    for column in ("", "Accuracy", "Inaccuracies", "Mistakes", "Blunders"):
        summary.add_column(column)
    for label, color in (("You", game.user_color), ("Opponent", game.opponent_color)):
        accuracy = analysis.accuracy(color)
        summary.add_row(
            label,
            "-" if accuracy is None else f"{accuracy:.1f}",
            *(str(analysis.count(color, move_class)) for move_class in _KEY_MOMENTS),
        )
    console.print(summary)

    mistakes = [
        m for m in analysis.moves if m.color is game.user_color and m.move_class in _KEY_MOMENTS
    ]
    if not mistakes:
        console.print("No inaccuracies, mistakes or blunders. Clean game!")
        return
    moments = Table(title="Your key moments")
    for column in ("Move", "Played", "Best", "Judgement", "Eval", "Win % lost", "Clock"):
        moments.add_column(column)
    for move in mistakes:
        moments.add_row(
            _move_number(move),
            move.san,
            move.best_move_san or "-",
            f"[{_CLASS_STYLE[move.move_class]}]{move.move_class.value}[/]",
            f"{_eval(move.eval_before)} → {_eval(move.eval_after)}",
            f"{move.win_pct_loss:.1f}",
            _clock(move.clock_seconds),
        )
    console.print(moments)


def _move_number(move: MoveAnalysis) -> str:
    number = move.ply // 2 + 1
    return f"{number}." if move.ply % 2 == 0 else f"{number}..."


def _eval(evaluation: Evaluation) -> str:
    if evaluation.mate_in is not None:
        return f"#{evaluation.mate_in}"
    return f"{(evaluation.centipawns or 0) / 100:+.2f}"


def _clock(seconds: float | None) -> str:
    if seconds is None:
        return "-"
    minutes, rest = divmod(int(seconds), 60)
    return f"{minutes}:{rest:02d}"


TOP_HIGHLIGHTS = 5


def show_reports(console: Console, reports: list[WrittenReport]) -> None:
    if not reports:
        console.print("No games for those time classes. Run `coach sync` first.")
        return
    for written in reports:
        console.print(
            f"\n[bold]{written.time_class.value}[/] ({written.games} games) → {written.location}"
        )
        if not written.highlights:
            console.print("  Nothing stands out yet.")
        for highlight in written.highlights[:TOP_HIGHLIGHTS]:
            marker = "[green]+[/]" if highlight.strength else "[red]-[/]"
            console.print(f"  {marker} {highlight.text}")
