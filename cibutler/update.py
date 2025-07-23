import typer
from rich.console import Console
from rich.panel import Panel
import rich.box
import time
import importlib
import logging
import os
import sys
import shlex
from pypi_simple import PyPISimple


import cibutler._version as _version
from cibutler._version import __version__ as cibutler_version
from cibutler import __app_name__

try:
    __version__ = importlib.metadata.version("cibutler")
except Exception:
    from cibutler._version import __version__

logger = logging.getLogger(__name__)

console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer()


def available_versions(
    index_url: str = typer.Option(
        "https://community.opengroup.org/api/v4/projects/1558/packages/pypi/simple",
        "--index-url",
        help="index-url",
    ),
    project: str = "cibutler",
):
    versions = ""
    with PyPISimple(endpoint=index_url) as client:
        requests_page = client.get_project_page(project)
        for package in requests_page.packages:
            # console.print(package.version)
            # versions.append(package.version)
            versions += f"{package.version.strip()} "
    return versions


@cli.command(rich_help_panel="Utility Commands")
def update(
    index_url: str = typer.Option(
        "https://community.opengroup.org/api/v4/projects/1558/packages/pypi/simple",
        "--index-url",
        help="index-url",
    ),
    project: str = "cibutler",
):
    """
    Update CI Butler :rocket:
    """
    command = f"exec pipx upgrade {project} --index-url {index_url.strip()}"
    os.system(command)


@cli.command(rich_help_panel="Utility Commands", name="version")
def version_command(
    index_url: str = typer.Option(
        "https://community.opengroup.org/api/v4/projects/1558/packages/pypi/simple",
        "--index-url",
        help="index-url",
    ),
    project: str = "cibutler",
    pre: bool = typer.Option(True, "--pre/--no-pre", help="Pre release"),
):
    """
    Version and Update information for cibutler :rocket:
    """
    text = f"""
    Currently running: {__app_name__} [green]v{__version__}[/green] ({cibutler_version})
    BuildTime: {time.ctime(_version.__buildtime__)}
    Branch: {_version.__branch__}
    CommitID: {_version.__commitid__}
    CommitMesage: {_version.__commitmessage__}
    CommitTimestamp: {_version.__committimestamp__}
    """
    # command_line = f"pip index versions {project} --index-url " + index_url.strip()
    # upgrade_command_line = (
    #    "pip install --upgrade cibutler --index-url " + index_url.strip()
    # )
    pipx_upgrade_command_line = (
        f"pipx upgrade {project} --index-url " + index_url.strip()
    )
    pipx_upgrade_command_line_with_shared_libs = (
        f"pipx upgrade {project} --index-url "
        + index_url.strip()
        + ' --pip-args="--extra-index-url=https://community.opengroup.org/api/v4/projects/148/packages/pypi/simple"'
    )

    pre_release_msg = ""
    if pre:
        # command_line = command_line + " --pre"
        # upgrade_command_line = upgrade_command_line + " --pre"
        pre_release_msg = "pre-release"

    # args = shlex.split(command_line)
    # try:
    #    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #    stdout, stderr = p.communicate()
    # except FileNotFoundError:
    #    error_console.print("Error: Unable to locate Pip")
    #    raise typer.Exit(3)

    output = available_versions(index_url=index_url, project=project)

    console.print(
        Panel(text, box=rich.box.SQUARE, expand=True, title="[green]Current[/green]")
    )
    # console.print(stdout.decode())
    console.print(
        Panel(
            "\n" + output,
            box=rich.box.SQUARE,
            expand=True,
            title=f"[green]Available from [/green][cyan]{index_url}[/cyan]",
        )
    )

    console.print(
        Panel(
            f"\n Run [green]cibutler update[/green] or use pipx update command:\n\n [green]{pipx_upgrade_command_line}[/green]"
            + f"\n\nPipx update command with shared libraries (OSDU Python SDK):\n\n [green]{pipx_upgrade_command_line_with_shared_libs}[/green]",
            box=rich.box.SQUARE,
            expand=True,
            title=f"[yellow]To upgrade your system to latest {pre_release_msg}[/yellow]",
        )
    )
