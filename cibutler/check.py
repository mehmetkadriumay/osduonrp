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


@cli.command(rich_help_panel="CI Commands")
def check(
    target: Annotated[str, typer.Option(help="Target")] = None,
):
    """
    Install Preflight Check
    """
    if target is None:
        options = [
            "Minikube running inside docker",
            "Kubernetes (kubeadm) running in docker-desktop",
            "MicroK8s on this machine",
            "Other Kubernetes Cluster",
        ]
        questions = [
            inquirer.List(
                "target",
                message="Where do you want to install?",
                choices=options,
            ),
        ]
        answers = inquirer.prompt(questions)
        target = str(answers["target"])

    console.print(f"Target: {target}")
    console.print(f"Platform: {platform.platform()} CPU: {utils.cpu_info()}")

    if "minikube" in target.lower():
        cimpl.check_hosts()
    elif "docker-desktop" in target.lower():
        preflight_check_required()
        k8s_checks()
        cimpl.check_hosts()
    elif "microk8s" in target.lower():
        preflight_check_required(skip_docker_daemon=True, skip_docker=True)
        k8s_checks()
        cimpl.check_hosts()
    elif "other kubernetes" in target.lower():
        preflight_check_required(
            skip_docker_daemon=True, skip_docker=True, min_cpu_cores=2
        )
        k8s_checks()
        cimpl.check_hosts()
    else:
        error_console.print(f":x: Unknown target: {target}")
        raise typer.Exit(1)


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
        ram = cidocker.docker_info_memtotal()
        if ram == 0:
            error_console.print(
                ":x: Error getting RAM setting. Is the docker daemon running?"
            )
            raise typer.Exit(1)
        mem_gb = ram / 1024 / 1024 / 1024
        if total_heap_required > mem_gb:
            error_console.print(
                f":x: Not enough RAM configured for docker. Found {memory} but {total_heap_required} GiB recommended"
            )
        else:
            console.print(
                f":white_check_mark: Docker Reporting enough RAM for install {memory} :thumbs_up:"
            )


def k8s_checks(required_cores=4, required_ram=23.2):
    info = cik8s.cluster_info()
    if info.count("running") >= 2:
        console.print(":white_check_mark: Kubernetes cluster running :thumbs_up:")
    else:
        error_console.print(":x: Kubernetes may not be running:")
        print(info)
        raise typer.Exit(1)

    cores = cik8s.kube_allocatable_cpu()
    if cores >= required_cores:
        console.print(f":white_check_mark: Kubernetes CPU cores {cores} :thumbs_up:")
    else:
        error_console.print(f":x: Not enough CPU {cores} given to kubernetes")
        raise typer.Exit(1)

    k8s_memory = cik8s.kube_allocatable_memory()
    if k8s_memory.endswith("Ki"):
        ki = int(k8s_memory.replace("Ki", ""))
        gb = ki / 1024 / 1024
        if gb >= required_ram:
            console.print(
                f":white_check_mark: Allocatable RAM {gb:.2f} GiB :thumbs_up:"
            )
        else:
            error_console.print(
                f":x: Not enough Allocatable RAM for {gb:.2f} kubernetes"
            )
        raise typer.Exit(1)

    num_ready = int(cik8s.kube_istio_ready().split()[0])
    if num_ready >= 1:
        console.print(":white_check_mark: istio ready :thumbs_up:")
    else:
        error_console.print(":x: istio not ready")
        raise typer.Exit(1)


if __name__ == "__main__":
    cli()
