import subprocess
from rich.console import Console
import typer

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
    return int(docker_info(outputformat="{{json .NCPU}}"))


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
    else:
        return output.stdout.decode("ascii").strip()


@diag_cli.command(
    rich_help_panel="Docker Diagnostic Commands", name="docker-info"
)
def get_docker_info(output: str = "json"):
    """
    Get Docker info
    """
    console.print_json(docker_info(outputformat=output))
