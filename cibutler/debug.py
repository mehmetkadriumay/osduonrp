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
import cibutler.cihelm as cihelm

logger = logging.getLogger(__name__)

console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

diag_cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)


@diag_cli.command(rich_help_panel="CI Butler Diagnostic Commands", name="debug")
def partition_debug(
    host: Annotated[str, typer.Option(help="host")] = "localhost",
    save: Annotated[bool, typer.Option(help="Save to file")] = False,
):
    """
    Debug the CImpl installation by checking the partition service.
    """
    name = "partition_service_response.json"
    try:
        response = requests.get(f"http://osdu.{host}/api/partition/v1/partitions/osdu")
    except requests.RequestException as e:
        error_console.print(f":x: Error connecting to partition service: {e}")
        logger.error(f"Error connecting to partition service: {e}")
        return None

    if response.status_code != 200:
        error_console.print(
            f":x: Error connecting to partition service at http://osdu.{host}/api/partition/v1/partitions/osdu"
        )
        logger.error(
            f"Error connecting to partition service at http://osdu.{host}/api/partition/v1/partitions/osdu"
        )
        return None

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


@diag_cli.command(rich_help_panel="CI Butler Diagnostic Commands", deprecated=True)
def package():
    """This is a deprecated command. Use `cibutler diag inspect` instead."""
    inspect()


@diag_cli.command(rich_help_panel="CI Butler Diagnostic Commands")
def inspect(
    force: Annotated[
        bool, typer.Option("--force", "--yes", help="No confirmation prompt")
    ] = False,

):
    """
    Report CIButler diagnostics into a zip file.

    This command will inspect your installation. It will create a zip of logs and traces which can
    be attached to an issue filed against the CI Butler project.
    """
    namespace = "default"
    home = str(Path.home())

    context = cik8s.get_currentcontext()
    if context is None:
        error_console.print(
            ":x: No current context set. Please run `cibutler use-context` to set the current context."
        )
        return
    elif "minikube" in context:
        console.print(":warning: Minikube detected. Please make sure you have tunnel running.", style="bold yellow")
        if not force:
            typer.confirm("Confirm tunnel is running?", abort=True)


    cik8s.log_kube_stats()

    not_running_file = cik8s.pods_not_running(namespace=namespace, save=True)
    services_file = cik8s.services(namespace=namespace, save=True)
    partition_file = partition_debug(save=True)
    storage_classes_file = cik8s.get_storage_classes(save=True)
    list_pods_file, list_pods_json_file = cik8s.list_pods(save=True)
    cik8s.describe(what="nodes", namespace=namespace, save=True)
    helm_list_file = cihelm.helm_list_command(save=True)

    with console.status("Packaging diagnostics..."):
        with ZipFile("cibutler.zip", "w") as zip:
            if partition_file:
                zip.write(partition_file)
            if list_pods_file:
                zip.write(list_pods_file)
            if list_pods_json_file:
                zip.write(list_pods_json_file)
            if not_running_file:
                zip.write(not_running_file)
            if services_file:
                zip.write(services_file)
            if storage_classes_file:
                zip.write(storage_classes_file)
            if helm_list_file:
                zip.write(helm_list_file)
            for file in os.listdir("."):
                if file.endswith("_describe.txt") or file.endswith("_logs.txt"):
                    zip.write(file)
                    os.remove(file)
            zip.write(f"{home}/cibutler.log")
            console.print(":package: Report packaged into cibutler.zip")

    with console.status("Cleaning up..."):
        if partition_file:
            os.remove(partition_file)
        if list_pods_file:
            os.remove(list_pods_file)
        if list_pods_json_file:
            os.remove(list_pods_json_file)
        if not_running_file:
            os.remove(not_running_file)
        if storage_classes_file:
            os.remove(storage_classes_file)
        if services_file:
            os.remove(services_file)
        if helm_list_file:
            os.remove(helm_list_file)


if __name__ == "__main__":
    diag_cli()
