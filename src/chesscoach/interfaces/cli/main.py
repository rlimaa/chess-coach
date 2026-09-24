from datetime import datetime
from typing import Annotated

import typer
import uvicorn
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn

from chesscoach.application.dto import GameFilter
from chesscoach.application.errors import (
    GameNotAnalyzedError,
    GameNotFoundError,
    GameSourceError,
    PlayerNotFoundError,
)
from chesscoach.config import load_settings
from chesscoach.container import Container
from chesscoach.domain.value_objects import TimeClass
from chesscoach.interfaces.cli import presenters
from chesscoach.interfaces.web.app import create_app

app = typer.Typer(help="Your personal chess coach.", no_args_is_help=True)
console = Console()

UsernameOption = Annotated[
    str | None, typer.Option("--username", "-u", help="chess.com username (default: from config).")
]
TimeClassOption = Annotated[
    TimeClass | None, typer.Option("--time-class", "-t", help="Only this time class.")
]


def _container() -> Container:
    return Container(load_settings())


def _fail(message: str) -> typer.Exit:
    presenters.show_error(console, message)
    return typer.Exit(code=1)


def _resolve_username(container: Container, username: str | None) -> str:
    resolved = username or container.settings.chesscom_username
    if not resolved:
        raise _fail("No chess.com username. Set CHESSCOM_USERNAME in .env or pass --username.")
    return resolved


@app.callback()
def main() -> None:
    """Your personal chess coach."""


@app.command("engine-check")
def engine_check() -> None:
    """Verify that Stockfish starts and evaluates the start position."""
    try:
        probe = _container().probe_engine()
    except FileNotFoundError as error:
        raise _fail(str(error)) from error
    presenters.show_engine_probe(console, probe)


@app.command()
def sync(username: UsernameOption = None) -> None:
    """Import your games from chess.com (only new months after the first run)."""
    container = _container()
    player = _resolve_username(container, username)
    try:
        with console.status(f"Syncing games of {player} from chess.com..."):
            report = container.sync_games().execute(player)
    except PlayerNotFoundError as error:
        raise _fail(f"Player '{player}' not found on chess.com.") from error
    except GameSourceError as error:
        raise _fail(f"chess.com request failed: {error}") from error
    presenters.show_sync_report(console, player, report)


@app.command()
def stats(
    username: UsernameOption = None,
    time_class: TimeClassOption = None,
) -> None:
    """Show results, ratings and openings from your imported games."""
    container = _container()
    player = _resolve_username(container, username)
    presenters.show_stats(console, container.get_stats().execute(player, time_class=time_class))


@app.command()
def analyze(
    username: UsernameOption = None,
    last: Annotated[int, typer.Option("--last", "-n", help="How many recent games.")] = 20,
    depth: Annotated[
        int | None, typer.Option("--depth", "-d", help="Engine depth (default: from config).")
    ] = None,
    time_class: TimeClassOption = None,
    since: Annotated[
        datetime | None,
        typer.Option(
            "--since",
            help="Only games played on or after this date (YYYY-MM-DD).",
            formats=["%Y-%m-%d"],
        ),
    ] = None,
) -> None:
    """Analyze your most recent unanalyzed games with Stockfish."""
    container = _container()
    player = _resolve_username(container, username)
    depth = depth or container.settings.engine.depth
    progress = Progress(
        TextColumn("{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    )
    try:
        with container.analysis_session() as analyze_games, progress:
            task = progress.add_task("Analyzing", total=None)
            report = analyze_games.execute(
                player,
                limit=last,
                depth=depth,
                only=GameFilter(time_class, since.date() if since else None),
                on_progress=lambda game, done, total: progress.update(
                    task, completed=done, total=total, description=game.opponent.username
                ),
            )
    except FileNotFoundError as error:
        raise _fail(str(error)) from error
    presenters.show_analyze_report(console, report, depth)


@app.command()
def game(
    reference: Annotated[str, typer.Argument(help="Game id, chess.com URL or URL number.")],
) -> None:
    """Review one analyzed game: accuracy and your worst moves."""
    try:
        review = _container().review_game().execute(reference)
    except GameNotFoundError as error:
        raise _fail(f"Game '{reference}' not found. Run `coach sync` first?") from error
    except GameNotAnalyzedError as error:
        raise _fail("That game is not analyzed yet. Run `coach analyze` first.") from error
    presenters.show_game_review(console, review)


DEFAULT_REPORT_TIME_CLASSES = [TimeClass.RAPID, TimeClass.BLITZ]


@app.command()
def report(
    username: UsernameOption = None,
    time_classes: Annotated[
        list[TimeClass] | None,
        typer.Option("--time-class", "-t", help="Repeat for several (default: rapid and blitz)."),
    ] = None,
) -> None:
    """Write coaching reports per time class to the reports folder."""
    container = _container()
    player = _resolve_username(container, username)
    reports = container.generate_report().execute(
        player, time_classes or DEFAULT_REPORT_TIME_CLASSES
    )
    presenters.show_reports(console, reports)


@app.command()
def puzzles(
    username: UsernameOption = None,
    time_class: TimeClassOption = None,
    count: Annotated[int, typer.Option("--count", "-n", help="Puzzles in this session.")] = 5,
    list_only: Annotated[bool, typer.Option("--list", help="Show due puzzles, no quiz.")] = False,
) -> None:
    """Train on positions where you went wrong in your own games."""
    container = _container()
    player = _resolve_username(container, username)
    due = container.next_puzzles().execute(player, time_class=time_class, limit=count)
    if not due:
        console.print("No puzzles due. Analyze more games or come back later.")
        return
    if list_only:
        presenters.show_puzzle_list(console, due)
        return

    solve, rules = container.solve_puzzle(), container.chess_rules()
    solved = 0
    for number, puzzle in enumerate(due, start=1):
        presenters.show_puzzle(
            console, puzzle, rules.render(puzzle.fen, puzzle.color), number, len(due)
        )
        result = solve.execute(puzzle, typer.prompt("Your move"))
        while not result.legal:
            console.print("That is not a legal move here. Try again.")
            result = solve.execute(puzzle, typer.prompt("Your move"))
        solved += result.correct
        presenters.show_puzzle_result(console, puzzle, result)
    console.print(f"\n{solved}/{len(due)} solved.")


@app.command()
def progress(
    time_class: Annotated[TimeClass, typer.Option("--time-class", "-t")],
    username: UsernameOption = None,
    days: Annotated[int, typer.Option("--days", "-d", help="Length of each period.")] = 30,
) -> None:
    """Compare the last N days with the N days before."""
    container = _container()
    player = _resolve_username(container, username)
    presenters.show_progress(
        console, container.compare_progress().execute(player, time_class, days)
    )


@app.command()
def web(
    host: Annotated[str, typer.Option("--host", help="Listen on this address.")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", help="Listen on this port.")] = 8000,
) -> None:
    """Run the web dashboard."""
    uvicorn.run(create_app(_container()), host=host, port=port)
