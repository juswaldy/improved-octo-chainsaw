"""Top-level Typer application wiring CLI commands."""

from __future__ import annotations

import importlib
from typing import Callable

import typer

CommandRegistrar = Callable[[typer.Typer], None]

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False,
    help="CLI surface for Hebrew Bible audio/text alignment workflows.",
)


def _register(module_path: str, registrar_name: str = "register") -> None:
    """Import *module_path* and invoke its registrar with the global app.

    Keeping registration lazy avoids import errors before dependencies (MFA, numpy, etc.)
    are installed and keeps startup costs low while we build out the CLI.
    """

    module = importlib.import_module(module_path)
    registrar: CommandRegistrar = getattr(module, registrar_name)
    registrar(app)


def _register_commands() -> None:
    _register("hb_align.cli.process")
    _register("hb_align.cli.review")
    _register("hb_align.cli.batch")


_register_commands()


def main() -> None:
    """Invoke the Typer application."""

    app()


if __name__ == "__main__":
    main()
