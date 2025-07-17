import typer
from rich.console import Console
import requests
import logging
from typing_extensions import Annotated

logger = logging.getLogger(__name__)

console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

diag_cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands")
def debug(
    host: Annotated[str, typer.Option(help="host")] = "localhost",
):
    """Debug the CImpl installation by checking the partition service."""
    response = requests.get(f"http://osdu.{host}/api/partition/v1/partitions/osdu")
    if response.status_code != 200:
        error_console.print(
            f":x: Error connecting to partition service at http://osdu.{host}/api/partition/v1/partitions/osdu"
        )
        logger.error(
            f"Error connecting to partition service at http://osdu.{host}/api/partition/v1/partitions/osdu"
        )
        return
    console.print(response.json())
    logger.info(f"Response from partition service: {response.json()}")


if __name__ == "__main__":
    diag_cli()
