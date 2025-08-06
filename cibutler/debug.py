import typer
from rich.console import Console
from rich.progress import Progress
import requests
import logging
from pathlib import Path
import os
from typing_extensions import Annotated
from zipfile import ZipFile
import cibutler.cik8s as cik8s

logger = logging.getLogger(__name__)

console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

diag_cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands", name="debug")
def partition_debug(
    host: Annotated[str, typer.Option(help="host")] = "localhost",
    save: Annotated[bool, typer.Option(help="Save to file")] = False,
):
    """
    Debug the CImpl installation by checking the partition service.
    """
    name = "partition_service_response.json"
    response = requests.get(f"http://osdu.{host}/api/partition/v1/partitions/osdu")
    if response.status_code != 200:
        error_console.print(
            f":x: Error connecting to partition service at http://osdu.{host}/api/partition/v1/partitions/osdu"
        )
        logger.error(
            f"Error connecting to partition service at http://osdu.{host}/api/partition/v1/partitions/osdu"
        )
        return

    if save:
        with open(name, "w") as f:
            f.write(response.text)
        console.print(
            f":white_check_mark: Response from partition service saved to {name}"
        )
        logger.info(f"Response from partition service saved to {name}")
        return name
    else:
        console.print(response.json())
        logger.info(f"Response from partition service: {response.json()}")


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands")
def package():
    """
    Package CIButler diagnostics into a zip file.
    """
    namespace = "default"
    home = str(Path.home())

    cik8s.log_kube_stats()

    not_running_file = cik8s.pods_not_running(namespace=namespace, save=True)
    services_file = cik8s.services(namespace=namespace, save=True)
    partition_file = partition_debug(save=True)
    storage_classes_file = cik8s.get_storage_classes(save=True)
    list_pods_file, list_pods_json_file = cik8s.list_pods(save=True)
    cik8s.describe(what="nodes", namespace=namespace, save=True)

    with console.status("Packaging diagnostics..."):
        with ZipFile("cibutler.zip", "w") as zip:
            zip.write(partition_file)
            zip.write(list_pods_file)
            zip.write(list_pods_json_file)
            zip.write(not_running_file)
            zip.write(services_file)
            zip.write(storage_classes_file)
            for file in os.listdir("."):
                if file.endswith("_describe.txt") or file.endswith("_logs.txt"):
                    zip.write(file)
                    os.remove(file)
            zip.write(f"{home}/cibutler.log")
            console.print(":package: Diagnostics packaged into cibutler.zip")

    with console.status("Cleaning up..."):
        os.remove(partition_file)
        os.remove(list_pods_file)
        os.remove(list_pods_json_file)
        os.remove(not_running_file)
        os.remove(storage_classes_file)
        os.remove(services_file)


if __name__ == "__main__":
    diag_cli()
