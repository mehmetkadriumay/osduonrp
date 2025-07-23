#!/usr/bin/env python3
# CI Butler Shane Hutchins
import typer
from typing_extensions import Annotated
from typing import Optional
from rich.console import Console
from rich.panel import Panel
import rich.box
from rich.prompt import Confirm
import time
from pathlib import Path
import platform
import importlib.metadata
import cibutler.downloader as downloader
import cibutler.utils as utils
import cibutler.cik8s as cik8s
import cibutler.key as key
import cibutler.cidocker as cidocker
import cibutler.ciminikube as ciminikube
import cibutler.check as check
from cibutler.istio import check_istio, install_istio
import cibutler.cimpl as cimpl
from cibutler.cimpl import (
    install_cimpl,
    update_services,
    helm_install_notebook,
    check_running,
    bootstrap_upload_data,
    get_data_load_option,
    data_load_callback,
)
import cibutler.osdu as osdu
import cibutler.releases as releases
import cibutler.cihelm as cihelm
import cibutler.docs as docs
import cibutler.update as update
import cibutler.cloud as cloud

# import cibutler.tf as tf
import cibutler.conf as conf
import cibutler.debug as cidebug
import cibutler.config as config
import cibutler.check as cicheck
import logging
from dotenv import load_dotenv
from cibutler._version import __version__ as cibutler_version

home = str(Path.home())
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(module)s %(funcName)s %(lineno)d %(message)s",
    filename=f"{home}/{conf.logfile}",
    filemode="a",
    encoding="utf-8",
)
logger = logging.getLogger("cibutler")

# loading variables from .env file
load_dotenv(Path.home().joinpath(".env.cibutler"))

console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich",
    help="CI Butler - an OSDU Community Implementation utility",
    no_args_is_help=True,
)

diag_cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

try:
    __version__ = importlib.metadata.version("cibutler")
except Exception:
    from cibutler._version import __version__

cli.add_typer(docs.cli, name="docs", help="Generate documentation", hidden=True)

diag_cli.registered_commands += osdu.diag_cli.registered_commands
diag_cli.registered_commands += key.diag_cli.registered_commands
diag_cli.registered_commands += cimpl.diag_cli.registered_commands
diag_cli.registered_commands += cihelm.diag_cli.registered_commands
diag_cli.registered_commands += cik8s.diag_cli.registered_commands
diag_cli.registered_commands += ciminikube.diag_cli.registered_commands
diag_cli.registered_commands += cidocker.diag_cli.registered_commands
diag_cli.registered_commands += cloud.diag_cli.registered_commands
# diag_cli.registered_commands += tf.diag_cli.registered_commands
diag_cli.registered_commands += cidebug.diag_cli.registered_commands
diag_cli.registered_commands += config.diag_cli.registered_commands

cli.add_typer(
    diag_cli,
    name="diag",
    help="System Insights and Advanced Diagnostics",
    rich_help_panel="Utility Commands",
)

cli.registered_commands += update.cli.registered_commands
cli.registered_commands += cik8s.cli.registered_commands
cli.registered_commands += cimpl.cli.registered_commands
cli.registered_commands += ciminikube.cli.registered_commands
cli.registered_commands += key.cli.registered_commands
cli.registered_commands += osdu.cli.registered_commands
cli.registered_commands += cihelm.cli.registered_commands
cli.registered_commands += cicheck.cli.registered_commands


def _version_callback(value: bool):
    if value:
        console.print(f"cibutler Version: {__version__} ({cibutler_version})")
        raise typer.Exit()


@diag_cli.command(rich_help_panel="Diagnostic Commands", hidden=True)
def logfile():
    """
    Automation for getting logfile
    """
    home = str(Path.home())
    console.print(f"{home}/{conf.logfile}")


@diag_cli.command(rich_help_panel="Helm Diagnostic Commands")
def helm_install(
    service_name: Annotated[str, typer.Option(help="OSDU service name")],
    name: Annotated[str, typer.Option(help="helm chart name")],
    force: Annotated[
        bool, typer.Option("--force", help="No confirmation prompt")
    ] = False,
    file: Path = typer.Option(
        "custom-values.yaml",
        "-f",
        "--file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
    chart: str = typer.Option(
        default="oci://community.opengroup.org:5555/osdu/platform/deployment-and-operations/infra-gcp-provisioning/gc-helm/osdu-gc-baremetal"
    ),
):
    """
    Helm install a service chart
    """
    if force or Confirm.ask(
        f"Chart: {chart}\nName: {name}\nFile: {file}\nInstall?", default=True
    ):
        console.print(cihelm.helm_install(name=name, file=file, chart=chart))


@cli.command(rich_help_panel="CI Commands")
def delete(
    force: Annotated[
        bool, typer.Option("--force", "--yes", "-y", help="No confirmation prompt")
    ] = False,
    profile: Annotated[str, typer.Option(hidden=True)] = None,
    minikube: Annotated[bool, typer.Option("-m", hidden=True)] = False,
):
    """
    Uninstall/Delete CImpl :skull:
    """
    if minikube:
        delete_minikube(force=force, profile=profile)
    else:
        context = cik8s.get_currentcontext()
        if context and "minikube" in context:
            delete_minikube(force=force, profile=profile)
        elif context:
            uninstall(force=force)
        else:
            error_console.print("Kubernetes context not set. Run 'use-context' first")
            raise typer.Abort()


def delete_minikube(force=False, profile=None):
    """
    Delete CImpl minikube and all data
    """
    if force or ask_delete():
        console.print("Deleting CImpl...")
        if profile:
            logger.info(f"Deleting minikube with profile: {profile}")
            ciminikube.minikube_delete(profile=profile)
        else:
            logger.info("Deleting minikube")
            ciminikube.minikube_delete()
        console.print("CImpl deleted successfully.")
    else:
        raise typer.Abort()


def ask_delete():
    """
    Ask user to confirm deletion
    """
    return Confirm.ask(
        "Are you sure you want to delete CImpl? This will remove all data and cannot be undone.",
        default=True,
    )


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands")
def uninstall(
    force: Annotated[
        bool, typer.Option("--force", "--yes", help="No confirmation prompt")
    ] = False,
    name: Annotated[str, typer.Option(help="CImpl Name")] = "osdu-cimpl",
    notebook_name: Annotated[
        str, typer.Option(help="Notebook Name")
    ] = "cimpl-notebook",
    namespace: Annotated[
        str,
        typer.Option("--namespace", "-n", help="Namespace where CImpl is installed"),
    ] = "default",
    istio_namespace: Annotated[
        str,
        typer.Option(
            "--istio-namespace", "-i", help="Namespace where istio is installed"
        ),
    ] = "istio-system",
):
    """
    Uninstall CImpl without deleting cluster
    """
    context = cik8s.get_currentcontext()
    if force or Confirm.ask(
        f"Uninstall CImpl {name}, notebook, istio and [red]anything else[/red] in namespace {namespace} of {context}?",
        default=True,
    ):
        console.print(
            "Note: kubernetes admin level resources (limits, quota, policy, authorization rules) will be ignored."
        )
        with console.status("Uninstalling helm charts..."):
            console.print(
                cihelm.helm_uninstall(name=notebook_name, namespace=namespace)
            )
            console.print(
                cihelm.helm_uninstall(name="bootstrap-data-deploy", namespace=namespace)
            )
            console.print(cihelm.helm_uninstall(name=name, namespace=namespace))
            console.print(
                cihelm.helm_uninstall(name="istio-ingress", namespace=istio_namespace)
            )
            console.print(
                cihelm.helm_uninstall(name="istio-base", namespace=istio_namespace)
            )
            console.print(
                cihelm.helm_uninstall(name="istiod", namespace=istio_namespace)
            )
        console.log("Cleaning up remaining...")
        with console.status("Deleting remaining secrets..."):
            console.print(cik8s.delete_item("secret"))
        with console.status("Deleting remaining deployments..."):
            console.print(cik8s.delete_item("deployments"))

        with console.status("Patching all PVCs"):
            cik8s.patch_all_pvcs(namespace=namespace)

        # with console.status("Deleting remaining pvc..."):
        # console.print(cik8s.delete_item("pvc"))
        with console.status(f"Deleting everything else in {namespace}..."):
            console.print(cik8s.delete_all(namespace=namespace))
        with console.status(f"Deleting everything else in {istio_namespace}..."):
            console.print(cik8s.delete_all(namespace=istio_namespace))
    else:
        raise typer.Abort()


@cli.command(rich_help_panel="OSDU Related Commands")
def envfile(
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = "http://osdu.localhost",
):
    """
    Download postman env file from local OSDU config service.

    envfile does not currently support protected endpoints
    """
    base_url = base_url.rstrip("/")
    url = base_url + "/api/config/v1/postman-environment"
    downloader.download([url], "./")


@diag_cli.command(rich_help_panel="Related Commands", hidden=True)
def success_message(
    version: str,
    source: str,
    minikube: bool,
    max_memory: bool,
    max_cpu: bool,
    duration_str: str,
    percent_memory: float,
    disk_size: int,
):
    allocatable_gb_memory = cik8s.kube_allocatable_memory_gb()
    capacity_gb_memory = cik8s.kube_capacity_memory_gb()
    allocatable_cpu = cik8s.kube_allocatable_cpu()

    output = f"""
    [yellow]Please report the following information to #cap-cibutler slack channel:[/yellow]

    [green]CImpl Installation Summary:[/green]
    [bold]CIButler Version:[/bold] {__version__} {cibutler_version}
    [bold]Platform:[/bold] {platform.platform()}
    [bold]Helm Version:[/bold] {version}
    [bold]Helm Source:[/bold] {source}
    [bold]Installation time:[/bold] {duration_str}
    [bold]Minikube:[/bold] {minikube}, [bold]Kubernetes:[/bold] {not minikube}
    [bold]Kubernetes RAM:[/bold] {allocatable_gb_memory:.2f}/{capacity_gb_memory:.2f} GiB [bold]CPU:[/bold] {allocatable_cpu}
    """
    if minikube:
        output += f"Minikube %RAM: {percent_memory}, MaxCPU: {max_cpu}, MaxMem: {max_memory}, Disk Size: {disk_size} GB"

    console.print(
        Panel(
            output,
            box=rich.box.SQUARE,
            expand=True,
            title="[cyan]OSDU Install Success - Please Report[/cyan]",
        )
    )


@cli.command(rich_help_panel="CI Commands")
def install(
    version: Annotated[
        str, typer.Option(help="CImpl version", envvar="HELM_VERSION")
    ] = None,
    source: Annotated[
        str, typer.Option(help="CImpl source", envvar="HELM_SOURCE")
    ] = None,
    notebook_source: Annotated[
        str, typer.Option(help="Notebook source")
    ] = "oci://us-central1-docker.pkg.dev/or2-msq-gnrg-osdu-mp-t1iylu/cimpl/helm/cimpl-notebook",
    notebook_version: Annotated[str, typer.Option(help="Notebook version")] = "0.0.1",
    install_notebook: Annotated[
        bool,
        typer.Option("--install-notebook/--skip-notebook", help="Install notebook"),
    ] = True,
    data_source: Annotated[
        str, typer.Option(help="Data load source")
    ] = "oci://community.opengroup.org:5555/osdu/platform/deployment-and-operations/base-containers-gcp/bootstrap-data/gc-helm/gc-bootstrap-data-deploy",
    data_version: Annotated[
        str, typer.Option(help="Data load version")
    ] = "0.0.7-gc3b0880b8",
    data_load_flag: Annotated[
        str,
        typer.Option(
            "--data-load-flag",
            "-d",
            callback=data_load_callback,
            help="Data load option",
        ),
    ] = None,
    percent_memory: Annotated[
        float, typer.Option(help="What percent of docker memory should be allocated")
    ] = 0.98,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Less output / for non-interactive use"),
    ] = False,
    max_cpu: Annotated[
        bool,
        typer.Option("--max-cpu", help="Let minikube use max CPU available in docker"),
    ] = False,
    max_memory: Annotated[
        bool,
        typer.Option(
            "--max-memory", help="Let minikube use max memory available in docker"
        ),
    ] = False,
    wait_for_complete: Annotated[
        bool, typer.Option("--wait", help="Monitor data load")
    ] = True,
    disk_size: Annotated[
        int, typer.Option(help="Disk size allocated to the minikube VM in GB")
    ] = 120,
    max_wait: Annotated[
        int, typer.Option(help="Maximum wait time for OSDU install in minutes")
    ] = 50,
    force: Annotated[
        bool, typer.Option("--force", "--yes", "-y", help="Attempt to force install")
    ] = False,
    minikube: Annotated[
        bool,
        typer.Option(
            "--minikube/--kubernetes",
            "-m/-k",
            help="Deploy Minikube (in Docker) or existing kubernetes cluster",
        ),
    ] = None,
    debug: Annotated[bool, typer.Option(help="Debug", hidden=True)] = False,
):
    """
    Install CImpli using minikube or kubernetes cluster, install notebook and data load. :rocket:

    Source can be an OCI registry or local path.

    data-load-flag options:
    'dd-reference', 'partial-dd-reference', 'tno-volve-reference', 'all', 'skip'
    Leaving data-load-flag will cause install to prompt for value

    """

    # if (
    #    minikube
    #    or "docker-desktop" in cik8s.get_current_valid_context()
    #    or "minikube" in cik8s.get_current_valid_context()
    # ):
    #    """
    #    If using minikube or docker-desktop as target then let's use
    #    arch of machine to give hints as to what container build would run
    #    best for CImpl. Otherwise assume that the kubernetes cluster
    #    is using X86 architecture.
    #    """
    #    arch = platform.machine()
    #    if arch == "arm64" or arch == "aarch64":
    #        console.print(":sparkles: Running on ARM architecture")
    #        arm = True
    #    else:
    #        console.print(":sparkles: Running on x86 architecture")

    if force:
        if minikube is None:
            error_console.print(
                "Target not selected, '--minikube' or '--kubernetes' required"
            )
            raise typer.Exit(1)
        configured_options = config.config(defaults=True)
    else:
        target = check.check()
        if "minikube" in target.lower():
            minikube = True
        else:
            minikube = False

    if not version and not source:
        if force:
            console.print(":warning: No version or source provided.")
            version, source = releases.select_version(defaults=True)
        else:
            # If no version or source is provided, prompt user to select a version
            version, source = releases.select_version()

    if not data_load_flag:
        if force:
            data_load_flag = get_data_load_option(defaults=True)
            console.print(
                f":warning: No data load option provided, defaulting to {data_load_flag}"
            )
        else:
            data_load_flag = get_data_load_option()

    if minikube:
        mem_gb = cidocker.docker_mem_gb()
        if conf.total_heap_required > mem_gb:
            console.print(
                "[yellow]:warning: Due to low memory, enabling [/yellow]'max-memory'"
            )
            max_memory = True

    if not force:
        configured_options = config.config()
        console.print("The following options will be used for installation:")
        console.print(
            f"Installing CImpl version: {version} from: {source}\nwith data load option: {data_load_flag}"
        )
        console.print(f"Notebook source: {notebook_source} version: {notebook_version}")
        console.print(f"Data source: {data_source} version: {data_version}")
        console.print(f"Minikube: {minikube}, Kubernetes:{not minikube}")
        if minikube:
            console.print(
                f"Percent Memory: {percent_memory}, Max CPU: {max_cpu}, Max Memory: {max_memory}, Disk Size: {disk_size}GB"
            )
        console.print(f"Enabled OSDU Services: {configured_options['osdu_services']}")
        typer.confirm("Proceed with install?", abort=True)

    logger.info(
        f"Installing CImpl version: {version} from: {source} with data load option: {data_load_flag}"
    )
    logger.info(f"Notebook source: {notebook_source} version: {notebook_version}")
    logger.info(f"Data source: {data_source} version: {data_version}")
    logger.info(f"Minikube: {minikube}, Kubernetes:{not minikube}")
    logger.info(
        f"Percent Memory: {percent_memory}, Max CPU: {max_cpu}, Max Memory: {max_memory}, Disk Size: {disk_size}GB"
    )

    start = time.time()

    if minikube:
        ciminikube.config_minikube(
            percent_memory=percent_memory,
            max_memory=max_memory,
            max_cpu=max_cpu,
            disk_size=disk_size,
        )
        ciminikube.minikube_start(force=force)
        if ciminikube.minikube_status():
            error_console.print(":x: Minikube in error state")
            raise typer.Exit(1)
        else:
            console.print(":smile: Minikube OK")

    console.log("Checking if storage class is needed in Kubernetes...")
    cik8s.add_sc(ignore=True)

    if not check_istio() and not install_istio():
        logger.error("Installation of istio has failed")
        error_console.log("Installation istio has failed")
        cik8s.kube_log_node_info()
        raise typer.Exit(1)

    install_cimpl(version=version, source=source, configured_options=configured_options)

    update_services(debug=debug)

    if not check_running(
        minikube=minikube,
        version=version,
        entitlement_workaround=True,
        quiet=quiet,
        max_wait=max_wait,
    ):
        error_console.log(
            f"Installation of {version} has failed on {platform.platform()}"
        )
        logger.error(f"Installation of {version} has failed on {platform.platform()}")
        cik8s.kube_log_node_info()
        raise typer.Exit(1)

    duration = time.time() - start
    duration_str = utils.convert_time(duration)
    console.log(
        f"CImpl helm: {version} installed in {duration_str}.\nReady to install Notebook and Upload data\n"
    )

    cik8s.kube_log_node_info()

    success_message(
        version=version,
        source=source,
        minikube=minikube,
        max_memory=max_memory,
        max_cpu=max_cpu,
        duration_str=duration_str,
        percent_memory=percent_memory,
        disk_size=disk_size,
    )

    logger.info(
        f"CImpl helm: {version} installed in {duration_str} on {platform.platform()}. Ready to install Notebook and Upload data"
    )

    if install_notebook:
        helm_install_notebook(notebook_source=notebook_source, version=notebook_version)

    data_load(
        data_load_flag=data_load_flag,
        data_source=data_source,
        data_version=data_version,
        wait_for_complete=wait_for_complete,
    )
    duration = time.time() - start
    duration_str = utils.convert_time(duration)
    logger.info(f"Install command completed in {duration_str}")
    console.log(f"Install ({version}) command completed in {duration_str}")


def data_load(data_load_flag, data_source, data_version, wait_for_complete=True):
    load_work_products = False
    if data_load_flag and "skip" in data_load_flag:
        console.log("Skipping data load")
        return
    elif data_load_flag and "prompt" not in data_load_flag:
        if "all" in data_load_flag:
            load_work_products = True
        bootstrap_upload_data(
            data_load_flag=data_load_flag,
            source=data_source,
            version=data_version,
            load_work_products=load_work_products,
            wait_for_complete=wait_for_complete,
        )
    else:
        data_load_flag = get_data_load_option()
        if data_load_flag:
            if "all" in data_load_flag:
                load_work_products = True
            bootstrap_upload_data(
                data_load_flag=data_load_flag,
                source=data_source,
                version=data_version,
                load_work_products=load_work_products,
                wait_for_complete=wait_for_complete,
            )


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands")
def upload_data(
    data_source: Annotated[
        str, typer.Option(help="Data source")
    ] = "oci://community.opengroup.org:5555/osdu/platform/deployment-and-operations/base-containers-gcp/bootstrap-data/gc-helm/gc-bootstrap-data-deploy",
    data_version: Annotated[
        str, typer.Option(help="Data version")
    ] = "0.0.7-gc3b0880b8",
    data_load_flag: Annotated[str, typer.Option(help="Data load flag")] = None,
    wait_for_complete: Annotated[
        bool, typer.Option("--wait", help="Wait for complete")
    ] = True,
):
    """
    Upload data to CImpl
    """
    data_load(
        data_load_flag=data_load_flag,
        data_source=data_source,
        data_version=data_version,
        wait_for_complete=wait_for_complete,
    )


@cli.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            callback=_version_callback,
            help="Show the application's version and exit",
        ),
    ] = None,
):
    """
    Just for version callback
    """
    pass


if __name__ == "__main__":
    cli()
