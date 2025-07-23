import typer
from rich.console import Console
from typing_extensions import Annotated
import inquirer
import platform
import logging
import shutil
import cibutler.cimpl as cimpl
import cibutler.cik8s as cik8s
import cibutler.cidocker as cidocker
import cibutler.utils as utils

logger = logging.getLogger(__name__)

console = Console()
error_console = Console(stderr=True, style="bold red")

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
            "Minikube running inside docker (Supported)",
            "Kubernetes (Kubeadm) running in docker-desktop - single node cluster (Supported)",
            "MicroK8s on this device (Supported)",
            "Kubernetes (Kind) running in docker-desktop (Unsupported)",
            "K3s (Containerd) on this device (Unsupported)",
            "K3d on this device (Unsupported)",
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
    target = select_target(target=target)
    console.print(f"Platform: {platform.platform()} CPU: {utils.cpu_info()}")

    if "minikube" in target.lower():
        console.print(":white_check_mark: Minikube Selected")
        preflight_check_required()
        cimpl.check_hosts()
    elif "docker-desktop" in target.lower():
        console.print(":white_check_mark: Docker-Desktop Selected")
        cik8s.use_context(context="docker-desktop")
        preflight_check_required()
        k8s_checks()
        cimpl.check_hosts()
    elif "microk8s" in target.lower():
        console.print(":white_check_mark: MicroK8s Selected")
        preflight_check_required(skip_docker_daemon=True, skip_docker=True)
        k8s_checks()
        cimpl.check_hosts()
    elif "k3s" in target.lower():
        console.print(
            ":white_check_mark: K3s (Rancher Lab’s minimal Kubernetes distribution) Selected"
        )
        cik8s.use_context(context="default")
        preflight_check_required(skip_docker_daemon=True, skip_docker=True)
        k8s_checks()
        cimpl.check_hosts()
    elif "k3d" in target.lower():
        console.print(":white_check_mark: K3d (K3s in Docker) Selected")
        cimpl.check_hosts()
        preflight_check_required()
        cimpl.check_hosts()
    elif "other kubernetes" in target.lower():
        console.print(":white_check_mark: Other Kubernetes Selected")
        preflight_check_required(
            skip_docker_daemon=True, skip_docker=True, min_cpu_cores=2
        )
        k8s_checks(ignore_ram=True)
        cimpl.check_hosts()
    else:
        error_console.print(f":x: Unknown target: {target}")
        raise typer.Exit(1)
    return target


def preflight_check_required(
    skip_docker_daemon=False,
    skip_docker=False,
    total_heap_required=26,
    min_cpu_cores=6,
):
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
        for cmd in external_utils:
            cmd_path = shutil.which(cmd)
            if cmd_path:
                console.print(f":white_check_mark: {cmd} installed")
            else:
                error_console.print(f":x: {cmd} not installed or not found")

        # nprocs = utils.getconf_nprocs_online()
        nprocs = utils.cpu_count()
        if nprocs and nprocs >= min_cpu_cores:
            console.print(
                f":white_check_mark: Local CPU Cores online: {nprocs} :thumbs_up:"
            )
        else:
            error_console.print(f":x: Not enough CPU cores detected {nprocs}")

        if skip_docker_daemon:
            console.print(":warning: Skipping docker daemon checks")
            return

        ncpu = cidocker.docker_info_ncpu()
        if ncpu == 0:
            error_console.print(
                ":x: Error getting NCPU setting. Is the docker daemon running?"
            )
            raise typer.Exit(2)
        elif ncpu >= min_cpu_cores:
            console.print(f":white_check_mark: Docker CPU Limit: {ncpu} :thumbs_up:")
        else:
            error_console.print(
                f":x: Docker CPU Limit too low. Not enough CPU given to docker {ncpu}"
            )
            console.print(
                f"Please increase to a min. {min_cpu_cores}.\nIf you recently changed this value try restarting docker."
            )

        memory = utils.convert_size(cidocker.docker_info_memtotal())
        mem_gb = cidocker.docker_mem_gb()

        if total_heap_required > mem_gb:
            error_console.print(
                f":x: Not enough RAM configured for docker. Found {memory} but {total_heap_required} GiB recommended"
            )
        else:
            console.print(
                f":white_check_mark: Docker Reporting enough RAM for install {memory} :thumbs_up:"
            )
    return True


def k8s_checks(required_cores=4, required_ram=23.2, ignore_ram=False):
    info = cik8s.cluster_info()
    if info.count("running") >= 2:
        console.print(":white_check_mark: Kubernetes cluster running :thumbs_up:")
    else:
        error_console.print(":x: Kubernetes may not be running:")
        console.print(info)
        raise typer.Exit(1)

    cores = cik8s.kube_allocatable_cpu()
    console.print(f":info: Kubernetes CPU cores {cores}")
    if (isinstance(cores, int)) and cores >= required_cores:
        console.print(f":white_check_mark: Kubernetes CPU cores {cores} :thumbs_up:")
    elif (isinstance(cores, str)) and "m" in cores:
        console.print(f":warning: Kubernetes CPU cores {cores}")
    else:
        error_console.print(f":x: Not enough CPU {cores} given to kubernetes")
        raise typer.Exit(1)

    gb_memory = cik8s.kube_allocatable_memory_gb()
    if gb_memory >= required_ram:
        console.print(
            f":white_check_mark: Allocatable RAM {gb_memory:.2f} GiB :thumbs_up:"
        )
    elif ignore_ram:
        error_console.print(
            f":warning: Possible not enough Allocatable RAM {gb_memory:.2f} in kubernetes"
        )
    else:
        error_console.print(
            f":x: Not enough Allocatable RAM for {gb_memory:.2f} kubernetes"
        )
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
