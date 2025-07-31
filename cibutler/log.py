from rich.console import Console
import time
import logging
import typer
import os
from pathlib import Path
from typing_extensions import Annotated
import cibutler.conf as conf
import cibutler.utils as utils

logger = logging.getLogger(__name__)
console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

diag_cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)


@diag_cli.command(rich_help_panel="Diagnostic Commands", hidden=True)
def logfile():
    """
    Automation for getting logfile
    """
    home = str(Path.home())
    console.print(f"{home}/{conf.logfile}")


@diag_cli.command(rich_help_panel="CI Butler Diagnostic Commands")
def tail(
    file_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
        ),
    ] = f"{Path.home()}/{conf.logfile}",
):
    """
    tail a file (for log files)
    """
    flag = utils.GracefulExiter()
    with open(file_path, "r") as file:
        # Move the pointer to the end of the file
        file.seek(0, 2)
        while True:
            if flag.exit():
                raise typer.Exit()
            line = file.readline()
            if not line:
                time.sleep(0.1)  # Sleep briefly
                continue
            console.print(line.strip())


if __name__ == "__main__":
    diag_cli()
