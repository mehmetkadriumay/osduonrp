#!/usr/bin/env python3.11
import typer
from typing_extensions import Annotated
from rich.console import Console
import logging
from pathlib import Path
from typing import Optional
from tfparse import load_from_path

logger = logging.getLogger(__name__)

console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

diag_cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)


@diag_cli.command(rich_help_panel="Terraform Related Commands", hidden=True)
def tf(
    dir: Annotated[Optional[Path], typer.Option()] = None,
    keys: Annotated[bool, typer.Option()] = False,
):
    """
    Parse terraform files in directory
    """
    if dir is None:
        print("No config file")
        raise typer.Abort()
    elif dir.is_dir():
        parsed = load_from_path(dir)
        if keys:
            console.print(parsed.keys())
        else:
            console.print(parsed)


if __name__ == "__main__":
    diag_cli()
