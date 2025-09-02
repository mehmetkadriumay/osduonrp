import typer
from typing_extensions import Annotated
import inquirer
import platform
import logging
import shutil
import socket
from packaging.version import Version
import cibutler.cimpl as cimpl
import cibutler.cik8s as cik8s
import cibutler.cidocker as cidocker
import cibutler.utils as utils
import cibutler.ciminikube as ciminikube
import cibutler.update as update
from cibutler.common import console, error_console, save_console_text

logger = logging.getLogger(__name__)


cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

diag_cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)


@diag_cli.command(rich_help_panel="CI Commands", hidden=True)
def select_target(
    target: Annotated[str, typer.Option(help="Target")] = None,
):
    if target is None:
        options = [
            "Minikube running inside docker (Supported: All releases)",
            "Kubernetes (Kubeadm) running in docker-desktop - single node cluster (Partially Supported)",
            "MicroK8s on this device (Supported: 0.27, Partial 0.28)",
            "Kubernetes (Kind) running in docker-desktop (Unsupported)",
            "K3s (Containerd) on this device (Unsupported)",
            "K3d on this device (Supported: 0.27)",
            "Other Kubernetes Cluster (Unsupported)",
        ]
        questions = [
            inquirer.List(
                "target",
                message="Where do you plan to install?",
                choices=options,
            ),
        ]
        answers = inquirer.prompt(questions)
        target = str(answers["target"])
        console.print(f"Target: {target}")
    return target


@cli.command(rich_help_panel="CI Commands")
def check(
    target: Annotated[str, typer.Option(help="Target")] = None,
):
    """
    Install Preflight Check
    """
    update.update_message()
    target = select_target(target=target)
    console.rule()
    logger.info(f"Uname: {platform.uname()}")
    logger.info(f"Platform: {platform.platform()}")
    console.print(f"Platform: {platform.platform()}")
    cimpl.cpu()
    logger.info(f"Platform Version: {platform.version()}")

    if "Windows" in platform.system():
        logger.info(f"Platform Win32: {platform.win32_ver()}")

    console.print(f"Node: {platform.node()} host: {socket.gethostname()}")
    logger.info(f"Node: {platform.node()} host: {socket.gethostname()}")

    if "minikube" in target.lower():
        console.print(":white_check_mark: Minikube Selected")
        preflight_check_required()
        check_docker_server_version()
        check_docker_memory_consumption()
        cimpl.check_hosts()
        if ciminikube.status():
            error_console.print(":x: Minikube Already running")
            logger.error("Minikube already running")
        else:
            console.print(":white_check_mark: Minikube State OK (not running)")

    elif "docker-desktop" in target.lower():
        console.print(":white_check_mark: Docker-Desktop Selected")
        cik8s.use_context(context="docker-desktop")
        preflight_check_required()
        check_docker_server_version()
        check_docker_memory_consumption()
        k8s_checks()
        cimpl.check_hosts()
        check_storage_class(added_during_install=True)
    elif "microk8s" in target.lower():
        context = cik8s.get_currentcontext()
        console.print(f":white_check_mark: MicroK8s Selected with context {context}")
        preflight_check_required(skip_docker_daemon=True, skip_docker=True)
        k8s_checks()
        cimpl.check_hosts()
        check_storage_class(added_during_install=True)
    elif "k3s" in target.lower():
        console.print(
            ":white_check_mark: K3s (Rancher Lab’s minimal Kubernetes distribution) Selected"
        )
        cik8s.use_context(context="default")
        preflight_check_required(skip_docker_daemon=True, skip_docker=True)
        k8s_checks()
        cimpl.check_hosts()
        check_storage_class(added_during_install=False)
    elif "k3d" in target.lower():
        console.print(":white_check_mark: K3d (K3s in Docker) Selected")
        cimpl.check_hosts()
        check_docker_server_version()
        preflight_check_required()
        cimpl.check_hosts()
        check_storage_class(added_during_install=False)
    elif "other kubernetes" in target.lower():
        context = cik8s.get_currentcontext()
        console.print(
            f":white_check_mark: Other Kubernetes Selected with context {context}"
        )
        preflight_check_required(
            skip_docker_daemon=True, skip_docker=True, min_cpu_cores=2
        )
        k8s_checks(ignore_ram=True)
        cimpl.check_hosts()
        check_storage_class(added_during_install=False)
    else:
        error_console.print(f":x: Unknown target: {target}")
        raise typer.Exit(1)

    # host based tools required
    if "Linux" in platform.system():
        check_installed(["ip", "sudo"])
    elif "Darwin" in platform.system():
        check_installed(["sudo"])

    save_console_text()
    return target


def check_storage_class(added_during_install=False, name="standard"):
    """
    Check Kubernetes storage class
    """
    if added_during_install:
        if not cik8s.add_sc(ignore=True, preview=True, name=name):
            console.print(
                ":warning: Storage class required, but will be added during install."
            )
            return
    else:
        if not cik8s.add_sc(ignore=True, preview=True, name=name):
            console.print(
                f":x: Storage class {name} required. See [green]cibutler diag add-sc --help[/green]",
                style="bold red",
            )
            return

    console.print(f":white_check_mark: Storage class {name} exists.")


def check_docker_memory_consumption(required=26):
    """
    Check if memory is available in docker
    """
    mem_gb = cidocker.docker_mem_gb()
    used_gb = cidocker.docker_memory_consumption_gb()
    available_gb = mem_gb - used_gb
    if available_gb < required:
        error_console.print(
            f":x: Not enough RAM available in docker {available_gb:.2f} GiB but {required} GiB recommended."
        )
        logger.error(f"Not enough RAM available in docker {available_gb:.2f} GiB.")
    else:
        console.print(
            f":white_check_mark: Docker Reporting enough available RAM for install {available_gb:.2f} :thumbs_up:"
        )


def check_installed(external_utils):
    """
    Check if CLI is installed/in path
    """
    for cmd in external_utils:
        cmd_path = shutil.which(cmd)
        if cmd_path:
            console.print(f":white_check_mark: {cmd} installed")
            logger.info(f"{cmd} installed")
        else:
            console.print(f":x: {cmd} not installed or not found", style="bold red")
            logger.error(f"{cmd} not installed or not found")


def check_docker_server_version(required_version="28"):
    """
    Check docker server version
    """
    version = cidocker.server_version()
    if Version(version) > Version(required_version):
        console.print(f":white_check_mark: Docker server version OK {version}")
        return True
    else:
        console.print(
            f":x: Docker server version may be too old. Found {version}", style="yellow"
        )
        logger.warning(f"Docker server version may be too old. Found {version}")
        return False


def preflight_check_required(
    skip_docker_daemon=False,
    skip_docker=False,
    total_heap_required=28,
    min_cpu_cores=6,
):
    """
    Preinstall checks
    """
    if skip_docker:
        console.print(":warning: Skipping docker and minikube checks")
        external_utils = [
            "kubectl",
            "helm",
        ]
    else:
        external_utils = [
            "docker",
            "minikube",
            "kubectl",
            "helm",
        ]

    with console.status("Checking Requirements for install..."):
        check_installed(external_utils=external_utils)

        # nprocs = utils.getconf_nprocs_online()
        nprocs = utils.cpu_count()
        if nprocs and nprocs >= min_cpu_cores:
            console.print(
                f":white_check_mark: Local CPU Cores online: {nprocs} :thumbs_up:"
            )
            logger.info(f"Local CPU Cores online: {nprocs}")
        else:
            console.print(
                f":x: Not enough CPU cores detected {nprocs}", style="bold red"
            )
            logger.error(f"Not enough CPU cores detected {nprocs}")

        if skip_docker_daemon:
            console.print(":warning: Skipping docker daemon checks")
            logger.warning("Skipping docker daemon checks")
            return

        ncpu = cidocker.docker_info_ncpu()
        if ncpu == 0:
            console.print(
                ":x: Error getting NCPU setting. Is the docker daemon running?",
                style="bold red",
            )
            logger.error("Error getting NCPU setting. Is the docker daemon running?")
            raise typer.Exit(2)
        elif ncpu >= min_cpu_cores:
            console.print(f":white_check_mark: Docker CPU Limit: {ncpu} :thumbs_up:")
            logger.info(f"Docker CPU Limit: {ncpu}")
        else:
            console.print(
                f":x: Docker CPU Limit too low. Not enough CPU given to docker {ncpu}",
                style="bold red",
            )
            logger.error(
                f"Docker CPU Limit too low. Not enough CPU given to docker {ncpu}"
            )
            console.print(
                f"Please increase to a min. {min_cpu_cores}.\nIf you recently changed this value try restarting docker."
            )

        memory = utils.convert_size(cidocker.docker_info_memtotal())
        mem_gb = cidocker.docker_mem_gb()

        if total_heap_required > mem_gb:
            console.print(
                f":x: Not enough RAM configured for docker. Found {memory} but {total_heap_required} GiB recommended.",
                style="bold red",
            )
            logger.error(
                ":x: Not enough RAM configured for docker. Found {memory} but {total_heap_required} GiB recommended."
            )
        else:
            console.print(
                f":white_check_mark: Docker Reporting enough RAM for install {memory} :thumbs_up:"
            )
    return True


def k8s_checks(required_cores=4, required_ram=23.2, ignore_ram=False):
    logger.info("k8s_checks")
    info = cik8s.cluster_info()
    if info.count("running") >= 2:
        console.print(":white_check_mark: Kubernetes cluster running :thumbs_up:")
        logger.info("Kubernetes cluster running")
    else:
        console.print(":x: Kubernetes may not be running:", style="bold red")
        logger.error(f"Kubernetes may not be running: {info}")
        console.print(info)
        raise typer.Exit(1)

    cores = cik8s.kube_allocatable_cpu()
    console.print(f":information_source: Kubernetes CPU cores {cores}")
    logger.info(f"Kubernetes CPU cores {cores}")
    if (isinstance(cores, int)) and cores >= required_cores:
        console.print(f":white_check_mark: Kubernetes CPU cores {cores} :thumbs_up:")
    elif (isinstance(cores, str)) and "m" in cores:
        console.print(f":warning: Kubernetes CPU cores {cores}", style="yellow")
    else:
        console.print(
            f":x: Not enough CPU {cores} given to kubernetes", style="bold red"
        )
        raise typer.Exit(1)

    gb_memory = cik8s.kube_allocatable_memory_gb()
    if gb_memory >= required_ram:
        console.print(
            f":white_check_mark: Allocatable RAM {gb_memory:.2f} GiB :thumbs_up:"
        )
        logger.info(f"Allocatable RAM {gb_memory:.2f} GiB OK")
    elif ignore_ram:
        console.print(
            f":warning: Possible not enough Allocatable RAM {gb_memory:.2f} in kubernetes",
            style="bold red",
        )
        logger.warning(
            f"Possible not enough Allocatable RAM {gb_memory:.2f} in kubernetes"
        )
    else:
        console.print(
            f":x: Not enough Allocatable RAM for {gb_memory:.2f} kubernetes",
            style="bold red",
        )
        logger.error(f"Not enough Allocatable RAM for {gb_memory:.2f} kubernetes")
        raise typer.Exit(1)

    # num_ready = int(cik8s.kube_istio_ready().split()[0])
    # if num_ready >= 1:
    #    console.print(":white_check_mark: istio ready :thumbs_up:")
    # else:
    #    error_console.print(":x: istio not ready")
    #    raise typer.Exit(1)
    # return True


if __name__ == "__main__":
    cli()
