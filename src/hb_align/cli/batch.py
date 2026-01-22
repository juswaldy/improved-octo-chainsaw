"""Stub `hb-align batch` command wiring."""

from __future__ import annotations

from pathlib import Path

import typer

_NOT_IMPLEMENTED_MSG = "`hb-align batch` will land with User Story 3 (tasks T027–T033)."


def register(app: typer.Typer) -> None:
    @app.command("batch")
    def batch_command(  # pragma: no cover - stub command
        input_dir: Path = typer.Argument(..., help="Directory containing chapter audio files."),
        parallel: int = typer.Option(
            1, "--parallel", min=1, help="Maximum number of concurrent alignments."
        ),
        stop_on_fail: bool = typer.Option(
            False, "--stop-on-fail", help="Abort processing when a chapter fails."
        ),
    ) -> None:
        typer.secho(_NOT_IMPLEMENTED_MSG, fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
