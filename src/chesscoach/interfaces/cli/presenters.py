from rich.console import Console
from rich.table import Table

from chesscoach.adapters.engine.diagnostics import EngineProbe
from chesscoach.application.dto import PlayerStats, SyncReport
from chesscoach.domain.services.statistics import ResultSummary


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
