"""Stub `hb-align review` command wiring."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

_NOT_IMPLEMENTED_MSG = (
    "`hb-align review` will arrive with User Story 2 (tasks T021–T026)."
)


def register(app: typer.Typer) -> None:
    @app.command("review")
    def review_command(  # pragma: no cover - stub command
        input_path: Path = typer.Argument(..., help="Alignment CSV/JSON to inspect."),
        threshold: float = typer.Option(0.9, "--threshold", min=0.5, max=0.99),
        output: Optional[Path] = typer.Option(None, "--output", help="Optional export path."),
    ) -> None:
        typer.secho(_NOT_IMPLEMENTED_MSG, fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
