import subprocess
from subprocess import call
from rich.console import Console
from typing_extensions import Annotated
import typer
import platform
import logging
import os
import cibutler.utils as utils
import cibutler.cidocker as cidocker

logger = logging.getLogger(__name__)

console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

diag_cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)


def suggested_cpu():
    """
    Get suggested CPU core count
    """
    nprocs = utils.cpu_count()
    # alternative nprocs = utils.getconf_nprocs_online()
    if nprocs > 22:
        suggested_cpu_limit = 16
    elif nprocs > 16:
        suggested_cpu_limit = 12
    elif nprocs > 8:
        suggested_cpu_limit = 8
    elif nprocs > 6:
        suggested_cpu_limit = 6
    return suggested_cpu_limit


@diag_cli.command(rich_help_panel="Minikube Diagnostic Commands")
def config_minikube(
    profile: str = None,
    max_cpu: bool = False,
    max_memory: bool = False,
    percent_memory: float = 0.98,
    disk_size: int = 120,  # Disk size allocated to the minikube VM in GB
):
    """
    Configure minikube
    """
    if max_cpu:
        console.print(":fire: Setting minikube CPU limit to the max :rocket:")
        minikube_config_set("cpus", "max", profile=profile)
    else:
        if "Darwin" in platform.system():
            suggested_cpu_limit = utils.macos_performance_cores()
            console.print(
                f":information: Mac reports {suggested_cpu_limit} performance CPU cores"
            )
        else:
            suggested_cpu_limit = suggested_cpu()
            console.print(
                f":information: Calculated suggested limit {suggested_cpu_limit} CPU cores"
            )

        ncpu = cidocker.docker_info_ncpu()
        console.print(f":information: Docker reports {suggested_cpu_limit} CPU cores")
        if ncpu < suggested_cpu_limit:
            cpu_limit = ncpu
        else:
            cpu_limit = suggested_cpu_limit

        console.print(f":pushpin: Setting minikube CPU limit to {cpu_limit}")
        minikube_config_set("cpus", f"{cpu_limit}", profile=profile)

    if max_memory:
        console.print(":fire: Setting minikube Memory limit to the max :rocket:")
        minikube_config_set("memory", "max", profile=profile)
    else:
        ram = cidocker.docker_info_memtotal()
        mem_gb = ram / 1024 / 1024 / 1024
        console.print(f":information: Docker reports {mem_gb:.1f}GB of RAM")
        memory_min_gb = 26
        if mem_gb > 32:
            memory_limit = round(
                (mem_gb - memory_min_gb) * percent_memory + memory_min_gb - 1
            )
        else:
            memory_limit = memory_min_gb

        console.print(f":pushpin: Setting minikube Memory limit to {memory_limit}g")
        minikube_config_set("memory", f"{memory_limit}g", profile=profile)
    minikube_config_set("disk-size", f"{disk_size}g", profile=profile)


def minikube_config_set(
    property,
    value,
    profile: str = None,
):
    """
    Minikue config set
    """
    try:
        if profile:
            output = subprocess.run(
                ["minikube", "config", "set", property, value, "--profile", {profile}],
                capture_output=True,
            )
        else:
            output = subprocess.run(
                ["minikube", "config", "set", property, value],
                capture_output=True,
            )
    except subprocess.CalledProcessError as err:
        return str(err)
    except FileNotFoundError as err:
        error_console.print(f"Unexpected FileNotFoundError: {err}")
        logger.fatal(f"Unexpected FileNotFoundError: {err}")
        raise typer.Exit(1)
    else:
        return output.stdout.decode("ascii").strip()


def change_group(group_name):
    try:
        subprocess.run(["newgrp", group_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error changing group: {e}")


def minikube_start(
    profile: str = None,
    force: bool = False,
    container_runtime: str = "docker",
    kubernetes_version: str = "stable",
    nodes: int = 1,
):
    """
    Minkube start
    """
    force_opt = ""
    if force:
        force_opt = "--force"

    # might need a change_group("docker") for linux
    if profile:
        console.print(
            f":fire: Starting minikube ({profile}) with {container_runtime} {kubernetes_version} kubernetes with {nodes} node(s)..."
        )
        call(
            [
                "minikube",
                "start",
                f"--container-runtime={container_runtime}",
                f"--kubernetes-version={kubernetes_version}",
                f"--nodes={nodes}",
                f"--profile {profile}",
            ]
        )
        call(
            [
                "minikube",
                "kubectl",
                "--",
                "config",
                "use-context",
                "minikube",
                "--profile",
                profile,
            ]
        )
    else:
        console.print(
            f":fire: Starting minikube with {container_runtime} {kubernetes_version} kubernetes with {nodes} node(s)..."
        )
        if force_opt:
            console.print("[yellow]:warning:[/yellow] force start enabled")

        call(
            [
                "minikube",
                "start",
                f"--container-runtime={container_runtime}",
                f"--kubernetes-version={kubernetes_version}",
                f"--nodes={nodes}",
                force_opt,
            ]
        )
        call(["minikube", "kubectl", "--", "config", "use-context", "minikube"])


def minikube_delete(profile: str = None):
    """
    Minikube delete
    """
    if profile:
        logger.info(f"Deleting minikube profile: {profile}")
        call(["minikube", "delete", "-p", profile])
    else:
        logger.info("Deleting minikube")
        call(["minikube", "delete"])


def minikube_status(profile: str = None):
    """
    Display status of minikube and return exit status
    """
    if profile:
        return call(["minikube", "status", "-p", profile])
    else:
        return call(["minikube", "status"])


def status():
    """
    Return status of minikube
    True if running
    """
    p = subprocess.Popen(["minikube", "status"], stdout=subprocess.PIPE, text=True)
    p.wait()
    logger.info(f"minikube exit status code: {p.returncode}")
    return not p.returncode


@diag_cli.command(rich_help_panel="Diag CI Commands")
def show_network(
    localhost: Annotated[
        bool,
        typer.Option(
            "--localhost",
            "-l",
            help="display localhost instead of node",
        ),
    ] = False,
    network: Annotated[
        str,
        typer.Option(
            "--network",
            "-n",
            help="",
        ),
    ] = "minikube",
):
    """
    Network IP of network
    """
    if localhost:
        console.print(f"{platform.node()}:127.0.0.1")
    else:
        console.print(
            f"{platform.node()}:{cidocker.get_container_network_ip(network=network)}"
        )


@cli.command(rich_help_panel="CI Commands")
def tunnel(
    background: Annotated[
        bool,
        typer.Option(
            "--background",
            "-b",
            help="Run in background - supported only on Linux and MacOS",
        ),
    ] = False,
):
    """
    Minkube tunnel

    Creates a route to services deployed with type LoadBalancer and sets their Ingress to their ClusterIP.
    """

    if platform.system() != "Windows" and background and os.geteuid() == 0:
        logfile = "tunnel.log"
        with open(logfile, "w") as outfile:
            console.print(f"Starting background minikube tunnel, logfile: {logfile}")
            console.log(f"Starting background minikube tunnel, logfile: {logfile}")
            subprocess.Popen(
                ["minikube", "tunnel", "--alsologtostderr"],
                stdout=outfile,
                stderr=outfile,
            )
    else:
        logger.info("Starting minikube tunnel")
        call(["minikube", "tunnel", "--alsologtostderr"])


if __name__ == "__main__":
    cli()
