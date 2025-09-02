import subprocess

# from rich.progress import Progress
from rich.progress import track
import typer
import logging
import docker
from typing_extensions import Annotated
import cibutler.utils as utils
from cibutler.common import console, error_console

logger = logging.getLogger(__name__)

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

diag_cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

import json


def docker_memory_consumption_gb():
    return docker_memory_consumption() / 1024 / 1024 / 1024


@diag_cli.command(rich_help_panel="Docker Diagnostic Commands", hidden=True)
def docker_memory_consumption():
    """
    return total memory used by containers in bytes
    """
    client = docker.from_env()

    memory_usage_total = 0
    cache_usage_total = 0
    container_list = client.containers.list()

    for container in track(
        container_list, description="Getting existing container memory consumption..."
    ):
        try:
            stat = container.stats(stream=False, decode=None)
            memory_usage = stat["memory_stats"]["usage"]
            cache_usage = stat["memory_stats"]["stats"]["inactive_file"]
            memory_usage_total += memory_usage
            cache_usage_total += cache_usage
        except KeyError:
            continue
        except Exception as err:
            logger.error(f"unable to get stats of container {container.name} {err}")
            continue
    logger.info(
        f"Current docker container memory consumption: {utils.convert_size(memory_usage_total)}"
    )
    logger.info(
        f"Current docker container cache consumption: {utils.convert_size(cache_usage_total)}"
    )
    return memory_usage_total


@diag_cli.command(rich_help_panel="Docker Diagnostic Commands")
def container_ip(container_id: str = "minikube", network: str = None):
    """
    Inspect container to get network ip
    """
    console.print(get_container_network_ip(container_id=container_id, network=network))


def get_container_network_ip(container_id: str = "minikube", network: str = None):
    client = docker.from_env()
    container = client.api.inspect_container(container_id)
    if network:
        return container["NetworkSettings"]["Networks"][network]["IPAddress"]
    else:
        return container["NetworkSettings"]["Networks"]


def log_container_list():
    client = docker.from_env()
    for container in client.containers.list():
        logger.info(
            f"id: {container.id}, name: {container.name}, {container.image}, {container.status}"
        )


def server_version():
    client = docker.from_env()
    info = client.info()
    return info["ServerVersion"]


def log_network_list():
    client = docker.from_env()
    for network in client.networks.list():
        logger.info(
            f"Network ID: {network.short_id} Name: {network.name}, Attrs: {network.attrs['Scope']}, Containers: {network.containers} {network.attrs}"
        )


def log_volume_list():
    client = docker.from_env()
    for volume in client.volumes.list():
        logger.info(f"Volume ID: {volume.short_id} Name: {volume.name}, {volume.attrs}")


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


def docker_network_ls(outputformat: str = "json"):
    """
    Return docker info
    """
    try:
        output = subprocess.run(
            ["docker", "network", "ls", "--format", outputformat], capture_output=True
        )
    except subprocess.CalledProcessError as err:
        return str(err)
    except (IOError, OSError) as err:
        return str(err)
    else:
        return output.stdout.decode("ascii").strip()


def docker_info(outputformat: str = "json"):
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


@diag_cli.command(rich_help_panel="Docker Diagnostic Commands")
def docker_inspect(item: str = "minikube", outputformat: str = "json"):
    """
    Docker inspect

    docker inspect minikube | jq -r '.[].NetworkSettings.Networks.minikube.IPAddress'
    """
    console.print(get_docker_inspect(item=item, outputformat=outputformat))


def get_docker_inspect(item: str = "host", outputformat: str = "json"):
    """
    Return docker info
    """
    try:
        output = subprocess.run(
            ["docker", "inspect", item, "--format", outputformat], capture_output=True
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
def log_docker_details():
    """
    Log containers, networks and volumes
    """
    log_container_list()
    log_network_list()
    log_volume_list()


@diag_cli.command(rich_help_panel="Docker Diagnostic Commands")
def purge():
    """
    Purge all docker containers, images, volumes and networks
    """
    typer.confirm("Are you sure you want to purge everything?", abort=True)
    console.print("Purging all docker containers, images, volumes and networks...")
    try:
        subprocess.run(
            ["docker", "system", "prune", "-a", "-f", "--volumes"], check=True
        )
        console.print("Purge completed successfully.")
    except subprocess.CalledProcessError as err:
        error_console.print(f"Error during purge: {err}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    console.print(server_version())
