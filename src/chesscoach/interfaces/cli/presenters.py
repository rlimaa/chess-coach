"""Rendering of results for the terminal. Formatting only, no logic."""

from rich.console import Console
from rich.table import Table

from chesscoach.adapters.engine.diagnostics import EngineProbe


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
