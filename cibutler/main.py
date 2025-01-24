#!/usr/bin/env python3
# CI Butler Shane Hutchins
import typer
from typing_extensions import Annotated
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
import ruamel.yaml
import os
import time
from pathlib import Path
import shutil
import platform
import importlib.metadata
import cibutler.downloader as downloader
import cibutler.utils as utils
import cibutler.cik8s as cik8s
import cibutler.key as key
from cibutler.cidocker import docker_info, docker_info_memtotal, docker_info_ncpu
import cibutler.ciminikube as ciminikube
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
import cibutler.cihelm as cihelm
import cibutler.docs as docs
import cibutler.update as update

# from kubernetes.client import configuration
# from kubernetes.client.rest import ApiException

console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich",
    help="CI Butler - an OSDU Community Implementation utility",
    no_args_is_help=True,
)

try:
    __version__ = importlib.metadata.version("mypackage")
except Exception:
    from cibutler._version import __version__

cli.registered_commands += update.cli.registered_commands
cli.registered_commands += cik8s.cli.registered_commands
cli.registered_commands += cimpl.cli.registered_commands
cli.registered_commands += ciminikube.cli.registered_commands
cli.registered_commands += key.cli.registered_commands
cli.registered_commands += osdu.cli.registered_commands
cli.registered_commands += cihelm.cli.registered_commands
cli.add_typer(docs.cli, name="docs", help="Generate documentation", hidden=True)


def _version_callback(value: bool):
    if value:
        console.print(f"cibutler Version: {__version__}")
        raise typer.Exit()


def prompt(ask, password=True, default=None, length=8):
    while True:
        value = Prompt.ask(ask, default=default, password=password)
        if len(value) >= length:
            break
        console.print("[prompt.invalid]password too short")
    return value


@cli.command(rich_help_panel="CI Commands", hidden=True)
def configure(
    default_random_password: bool = typer.Option(
        False, "--random", help="Use random passwords"
    ),
):
    filename = "custom-values.yaml"
    url = "https://community.opengroup.org/osdu/platform/deployment-and-operations/infra-gcp-provisioning/-/raw/master/examples/simple_osdu_docker_desktop/custom-values.yaml"

    if os.path.isfile(filename):
        console.print(f"{filename} exists")
    else:
        downloader.download([url], "./")
    data = custom_values(filename=filename)
    if not data:
        error_console.print(f"Unable to read {filename}")
        raise typer.Exit(1)

    if default_random_password:
        minio_password = utils.random_password()
        keycloak_admin_password = utils.random_password()
        postgresql_password = utils.random_password()
        airflow_externaldb_password = utils.random_password()
        airflow_password = utils.random_password()
        elasticsearch_password = utils.random_password()
        rabbitmq_password = utils.random_password()
    else:
        minio_password = data["minio"]["auth"]["rootPassword"]
        keycloak_admin_password = data["keycloak"]["auth"]["adminPassword"]
        postgresql_password = data["postgresql"]["global"]["postgresql"]["auth"][
            "postgresPassword"
        ]
        airflow_externaldb_password = data["airflow"]["externalDatabase"]["password"]
        airflow_password = data["airflow"]["auth"]["password"]
        elasticsearch_password = data["elasticsearch"]["security"]["elasticPassword"]
        rabbitmq_password = data["rabbitmq"]["auth"]["password"]
    domain = data["global"]["domain"]
    limits_enabled = str(data["global"]["limitsEnabled"]).lower()

    useInternalServerUrl = "true"
    hide = True
    domain = Prompt.ask("Domain", default=domain)

    limits_enabled = Prompt.ask(
        "limitsEnabled", choices=["true", "false"], default=limits_enabled
    )
    keycloak_admin_password = prompt(
        "Keycloak Password", password=hide, default=keycloak_admin_password
    )
    minio_password = prompt("Minio Password", password=hide, default=minio_password)
    postgresql_password = prompt(
        "Postgresql Password", password=hide, default=postgresql_password
    )
    airflow_externaldb_password = prompt(
        "Airflow ExternalDB Password",
        password=hide,
        default=airflow_externaldb_password,
    )
    airflow_password = prompt(
        "Airflow Password", password=hide, default=airflow_password
    )
    elasticsearch_password = prompt(
        "ElasticSearch Password", password=hide, default=elasticsearch_password
    )
    rabbitmq_password = prompt(
        "RabbitMQ Password", password=hide, default=rabbitmq_password
    )
    use_internal_server_url = Prompt.ask(
        "useInternalServerUrl", choices=["true", "false"], default=useInternalServerUrl
    )

    data["global"]["domain"] = domain
    data["global"]["limitsEnabled"] = bool(limits_enabled)
    data["minio"]["auth"]["rootPassword"] = minio_password
    data["minio"]["useInternalServerUrl"] = bool(use_internal_server_url)
    data["keycloak"]["auth"]["adminPassword"] = keycloak_admin_password
    data["postgresql"]["global"]["postgresql"]["auth"][
        "postgresPassword"
    ] = postgresql_password
    data["airflow"]["externalDatabase"]["password"] = airflow_externaldb_password
    data["airflow"]["auth"]["password"] = airflow_password
    data["elasticsearch"]["security"]["elasticPassword"] = elasticsearch_password
    data["rabbitmq"]["auth"]["password"] = rabbitmq_password

    if Confirm.ask("Save?", default=True):
        with open(filename, "w") as file:
            yaml = ruamel.yaml.YAML()
            yaml.dump(data, file)
            console.print(f"Updated: {filename}")

    # if Confirm.ask("Install?", default=True):
    #    output = helm_install()
    #    console.print(output)


@cli.command(rich_help_panel="CI Commands", hidden=True)
def helm_install(
    service_name: Annotated[str, typer.Option(help="OSDU service name")],
    name: Annotated[str, typer.Option(help="helm chart name")],
    force: bool = typer.Option(False, "--force", help="No confirmation prompt"),
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
    if force or Confirm.ask(
        f"Chart: {chart}\nName: {name}\nFile: {file}\nInstall?", default=True
    ):
        console.print(cihelm.helm_install(name=name, file=file, chart=chart))


@cli.command(rich_help_panel="Troubleshooting Commands", deprecated=True)
def uninstall(
    name: str = typer.Option(default="osdu-cimpl"),
    force: bool = typer.Option(False, "--force", help="No confirmation prompt"),
):
    """
    Uninstall CImpl without deleting cluster
    """
    if force or Confirm.ask(f"Uninstall {name}?", default=True):
        console.print(cihelm.helm_uninstall(name))
        console.print(cik8s.delete_item("secret"))
        console.print(cik8s.delete_item("pvc"))


def custom_values(filename="custom-values.yaml"):
    try:
        with open(filename, "r") as config:
            # try:
            # data = yaml.safe_load(config)
            yaml = ruamel.yaml.YAML()
            data = yaml.load(config)
            # except yaml.YAMLError as err:
            # except yaml.YAMLError as err:
            #    print(err)
            # console.print(data)
            # yaml.dump(data, sys.stdout)
            return data
    except FileNotFoundError:
        error_console.print(f"File {filename} Not found")
        return None


@cli.command(rich_help_panel="OSDU Related Commands")
def envfile(
    domain: str = typer.Option(default="localhost"),
):
    """
    Download postman env file from OSDU config service
    """
    url = f"http://osdu.{domain}/api/config/v1/postman-environment"
    downloader.download([url], "./")


@cli.command(rich_help_panel="Troubleshooting Commands", name="docker-info")
def get_docker_info(output: str = "json"):
    """
    Get Docker info
    """
    console.print_json(docker_info(outputformat=output))


@cli.command(rich_help_panel="CI Commands")
def install(
    version: str = "0.27.0-local",
    source: str = "oci://us-central1-docker.pkg.dev/or2-msq-gnrg-osdu-mp-t1iylu/cimpl/helm/osdu-cimpl",
    notebook_source: str = "oci://us-central1-docker.pkg.dev/or2-msq-gnrg-osdu-mp-t1iylu/cimpl/helm/cimpl-notebook",
    notebook_version: str = "0.0.1",
    install_notebook: Annotated[bool, typer.Option(help="Install notebook")] = True,
    data_source: str = "oci://community.opengroup.org:5555/osdu/platform/deployment-and-operations/base-containers-gcp/bootstrap-data/gc-helm/gc-bootstrap-data-deploy",
    data_version: str = "0.0.7-gc3b0880b8",
    data_load_flag: Annotated[str, typer.Option(callback=data_load_callback)] = None,
    percent_memory: float = 0.98,
    quiet: Annotated[
        bool, typer.Option(help="Less output / for non-interactive use")
    ] = False,
    max_cpu: Annotated[
        bool, typer.Option(help="Let minikube use max CPU available in docker")
    ] = False,
    max_memory: Annotated[
        bool, typer.Option(help="Let minikube use max memory available in docker")
    ] = False,
    wait_for_complete: Annotated[bool, typer.Option(help="Monitor data load")] = True,
    disk_size: Annotated[
        int, typer.Option(help="Disk size allocated to the minikube VM in GB")
    ] = 120,
):
    """
    Install CImpli via minikube, install notebook and data load. :rocket:

    data-load-flag options:
    'dd-reference', 'partial-dd-reference', 'tno-volve-reference', 'all', 'skip'
    Leaving data-load-flag will cause install to prompt for value

    """
    start = time.time()
    ciminikube.config_minikube(
        percent_memory=percent_memory,
        max_memory=max_memory,
        max_cpu=max_cpu,
        disk_size=disk_size,
    )
    ciminikube.minikube_start()
    if not check_istio() and not install_istio():
        error_console.print("Installation has failed")
        raise typer.Exit(1)
    install_cimpl(version=version, source=source)
    update_services()
    if not check_running(entitlement_workaround=True, quiet=quiet):
        error_console.print("Installation has failed")
        raise typer.Exit(1)

    if install_notebook:
        helm_install_notebook(notebook_source=notebook_source, version=notebook_version)

    duration = time.time() - start
    duration_str = utils.convert_time(duration)
    console.print(f"CImpl installed in {duration_str}. Ready to Upload data")
    data_load(
        data_load_flag=data_load_flag,
        data_source=data_source,
        data_version=data_version,
        wait_for_complete=wait_for_complete,
    )
    duration = time.time() - start
    duration_str = utils.convert_time(duration)
    console.print(f"Install command completed in {duration_str}")


def data_load(data_load_flag, data_source, data_version, wait_for_complete=True):
    load_work_products = False
    if data_load_flag and "prompt" not in data_load_flag:
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


@cli.command(rich_help_panel="Troubleshooting Commands")
def upload_data(
    data_source: str = "oci://community.opengroup.org:5555/osdu/platform/deployment-and-operations/base-containers-gcp/bootstrap-data/gc-helm/gc-bootstrap-data-deploy",
    data_version: str = "0.0.7-gc3b0880b8",
    data_load_flag: str = None,
    wait_for_complete: bool = True,
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


@cli.command(rich_help_panel="Troubleshooting Commands")
def cpu():
    """
    Display CPU info
    """
    console.print(utils.cpu_info())
    console.print(f"Logic cores: {os.cpu_count()}")
    if "Darwin" in platform.system():
        console.print(f"Performance Cores: {utils.macos_performance_cores()}")


@cli.command(rich_help_panel="CI Commands")
def check(all: bool = False):
    """
    Install Preflight Check
    """
    console.print(f"Platform: {platform.platform()}")
    utils.cpu_info()
    preflight_checks()
    if all:
        post_checks()


def preflight_checks():
    total_heap_required = 26
    MIN_CPU_CORES = 6
    with console.status("Checking Requirements..."):
        external_utils = [
            "docker",
            "minikube",
            "kubectl",
            "helm",
        ]
        for cmd in external_utils:
            cmd_path = shutil.which(cmd)
            if cmd_path:
                console.print(f"{cmd} installed :heavy_check_mark:")
            else:
                error_console.print(f"{cmd} installed :x:")

        # nprocs = utils.getconf_nprocs_online()
        nprocs = utils.cpu_count()
        if nprocs and nprocs >= MIN_CPU_CORES:
            console.print(f"CPU Cores online: {nprocs} :thumbs_up:")
        else:
            error_console.print(f"Not enough CPU cores detected {nprocs} :x:")

        ncpu = docker_info_ncpu()
        if ncpu == 0:
            error_console.print(
                "Error getting NCPU setting. Is the docker daemon running?"
            )
            raise typer.Exit(1)
        elif ncpu >= MIN_CPU_CORES:
            console.print(f"Docker CPU Limit: {ncpu} :thumbs_up:")
        else:
            error_console.print(
                f"Docker CPU Limit too low. Not enough CPU given to docker {ncpu} :x:"
            )
            console.print(
                f"Please increase to a min. {MIN_CPU_CORES}.\nIf you recently changed this value try restarting docker."
            )

        memory = utils.convert_size(docker_info_memtotal())
        ram = docker_info_memtotal()
        if ram == 0:
            error_console.print(
                "Error getting RAM setting. Is the docker daemon running?"
            )
            raise typer.Exit(1)
        mem_gb = ram / 1024 / 1024 / 1024
        if total_heap_required > mem_gb:
            error_console.print(
                f"Not enough RAM configured for docker. Found {memory} but {total_heap_required} GiB recommended"
            )
        else:
            console.print(
                f"Docker Reporting enough RAM for install {memory} :thumbs_up:"
            )


def post_checks():
    info = cik8s.cluster_info()
    if info.count("running") >= 2:
        console.print("Kubernetes cluster running :thumbs_up:")
    else:
        error_console.print("Kubernetes may not be running:")
        print(info)
        raise typer.Exit(1)

    cores = cik8s.kube_allocatable_cpu()
    if cores >= 4:
        console.print(f"Kubernetes CPU cores {cores} :thumbs_up:")
    else:
        error_console.print(f"Not enough CPU {cores} given to docker/kubernetes")
        raise typer.Exit(1)

    k8s_memory = cik8s.kube_allocatable_memory()
    if k8s_memory.endswith("Ki"):
        ki = int(k8s_memory.replace("Ki", ""))
        gb = ki / 1024 / 1024
        if gb >= 23.2:
            console.print(f"Allocatable RAM {gb:.2f} GiB :thumbs_up:")
        else:
            error_console.print(f"Not enough Allocatable RAM for {gb:.2f} kubernetes")
        raise typer.Exit(1)

    num_ready = int(cik8s.kube_istio_ready().split()[0])
    if num_ready >= 1:
        console.print("istio ready :thumbs_up:")
    else:
        error_console.print("istio not ready")
        raise typer.Exit(1)


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
    pass


if __name__ == "__main__":
    cli()
