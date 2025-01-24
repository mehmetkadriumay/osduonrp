import subprocess
from subprocess import call
from rich.console import Console
import typer
import platform
from typing_extensions import Annotated
import cibutler.utils as utils
import cibutler.cidocker as cidocker

console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)


def suggested_cpu():
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


@cli.command(rich_help_panel="Troubleshoooting Commands")
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
    Return docker info
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
    else:
        return output.stdout.decode("ascii").strip()


def change_group(group_name):
    try:
        subprocess.run(["newgrp", group_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error changing group: {e}")


def minikube_start(
    profile: str = None,
    container_runtime: str = "docker",
    kubernetes_version: str = "stable",
    nodes: int = 1,
):
    # might need a change_group("docker") for linux
    if profile:
        console.print(
            f":fire: Starting minikube ({profile}) with {container_runtime} {kubernetes_version} kubernetes with {nodes} node(s)..."
        )
        call(
            f"minikube start --container-runtime={container_runtime} --kubernetes-version={kubernetes_version} --nodes={nodes} --profile {profile}",
            shell=True,
        )
        call(
            f"minikube kubectl -- config use-context minikube --profile {profile}",
            shell=True,
        )
    else:
        console.print(
            f":fire: Starting minikube with {container_runtime} {kubernetes_version} kubernetes with {nodes} node(s)..."
        )
        call(
            f"minikube start --container-runtime={container_runtime} --kubernetes-version={kubernetes_version} --nodes={nodes}",
            shell=True,
        )
        call(
            "minikube kubectl -- config use-context minikube",
            shell=True,
        )


def minikube_delete(profile: str = None):
    if profile:
        call(f"minikube delete -p {profile}", shell=True)
    else:
        call("minikube delete", shell=True)


def minikube_status(profile: str = None):
    if profile:
        call(f"minikube status -p {profile}", shell=True)
    else:
        call("minikube status", shell=True)


@cli.command(rich_help_panel="CI Commands")
def delete(
    force: Annotated[
        bool, typer.Option(prompt="Are you sure you want to delete the installation?")
    ],
    profile: Annotated[str, typer.Option()] = None,
):
    """
    Uninstall/Delete CImpl :skull:
    """
    if profile:
        minikube_delete(profile=profile)
    else:
        minikube_delete()


@cli.command(rich_help_panel="CI Commands")
def tunnel():
    """
    Access CI
    """
    call("minikube tunnel --alsologtostderr", shell=True)


if __name__ == "__main__":
    cli()
