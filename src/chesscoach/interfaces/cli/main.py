from typing import Annotated

import typer
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn

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

app = typer.Typer(help="Your personal chess coach.", no_args_is_help=True)
console = Console()

UsernameOption = Annotated[
    str | None, typer.Option("--username", "-u", help="chess.com username (default: from config).")
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
    time_class: Annotated[
        TimeClass | None, typer.Option("--time-class", "-t", help="Only this time class.")
    ] = None,
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
