import subprocess
from rich.console import Console
import typer
import logging

logger = logging.getLogger(__name__)

console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

diag_cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)


def docker_info_memtotal():
    """
    Return memory setting/allow to be used by docker
    """
    return int(docker_info(outputformat="{{json .MemTotal}}"))


def docker_info_ncpu():
    """
    Return Number of CPUs setting/allow to be used by docker
    """
    try:
        return int(docker_info(outputformat="{{json .NCPU}}"))
    except ValueError as err:
        logger.error(f"Error parsing NCPU from docker info: {err}")
        return 0


def docker_mem_gb():
    ram = docker_info_memtotal()
    if ram == 0:
        error_console.print(
            ":x: Error getting RAM setting. Is the docker daemon running?"
        )
        raise typer.Exit(1)
    mem_gb = ram / 1024 / 1024 / 1024
    return mem_gb


def docker_info(outputformat):
    """
    Return docker info
    """
    try:
        output = subprocess.run(
            ["docker", "info", "--format", outputformat], capture_output=True
        )
    except subprocess.CalledProcessError as err:
        return str(err)
    except (IOError, OSError) as err:
        return str(err)
    else:
        return output.stdout.decode("ascii").strip()


@diag_cli.command(rich_help_panel="Docker Diagnostic Commands", name="docker-info")
def get_docker_info(output: str = "json"):
    """
    Get Docker info
    """
    console.print_json(docker_info(outputformat=output))


@diag_cli.command(rich_help_panel="Docker Diagnostic Commands")
def purge():
    """
    Purge all containers, images, volumes and networks
    """
    typer.confirm("Are you sure you want to purge everything?", abort=True)
    console.print("Purging all containers, images, volumes and networks...")
    try:
        subprocess.run(
            ["docker", "system", "prune", "-a", "-f", "--volumes"], check=True
        )
        console.print("Purge completed successfully.")
    except subprocess.CalledProcessError as err:
        error_console.print(f"Error during purge: {err}")
        raise typer.Exit(code=1)
