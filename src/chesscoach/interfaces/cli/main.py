"""`coach` command-line interface."""

import typer
from rich.console import Console

from chesscoach.config import load_settings
from chesscoach.container import Container
from chesscoach.interfaces.cli import presenters

app = typer.Typer(help="Your personal chess coach.", no_args_is_help=True)
console = Console()


def _container() -> Container:
    return Container(load_settings())


@app.callback()
def main() -> None:
    """Your personal chess coach."""


@app.command("engine-check")
def engine_check() -> None:
    """Verify that Stockfish starts and evaluates the start position."""
    try:
        probe = _container().probe_engine()
    except FileNotFoundError as error:
        presenters.show_error(console, str(error))
        raise typer.Exit(code=1) from error
    presenters.show_engine_probe(console, probe)
