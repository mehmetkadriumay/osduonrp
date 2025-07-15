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
import cibutler.cidocker as cidocker
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
import cibutler.cloud as cloud
import cibutler.tf as tf
import logging
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(module)s %(funcName)s %(lineno)d %(message)s",
    filename="./cibutler.log",
    filemode="a",
    encoding="utf-8",
)
logger = logging.getLogger("cibutler")

# loading variables from .env file
load_dotenv()

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
    __version__ = importlib.metadata.version("mypackage")
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
diag_cli.registered_commands += tf.diag_cli.registered_commands

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


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands")
def configure(
    default_random_password: bool = typer.Option(
        True, "--random", help="Use random passwords"
    ),
    interactive: bool = typer.Option(True, "--prompt", help="Prompt for values"),
):
    """Configure CImpl custom values file  :wrench:"""
    filename = "values.yaml"
    # url = "https://community.opengroup.org/osdu/platform/deployment-and-operations/infra-gcp-provisioning/-/raw/master/examples/simple_osdu_docker_desktop/custom-values.yaml"
    url = "https://community.opengroup.org/osdu/platform/deployment-and-operations/base-containers-cimpl/osdu-cimpl-stack/-/raw/main/helm/values.yaml"

    if os.path.isfile(filename):
        console.print(f"{filename} exists")
    else:
        downloader.download([url], "./")
    data = custom_values(filename=filename)
    if not data:
        error_console.print(f"Unable to read {filename}")
        raise typer.Exit(1)

    try:
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
            # keycloak_admin_password = data["keycloak"]["auth"]["adminPassword"]
            postgresql_password = data["postgresql"]["global"]["postgresql"]["auth"][
                "postgresPassword"
            ]
            airflow_externaldb_password = data["airflow"]["externalDatabase"][
                "password"
            ]
            airflow_password = data["airflow"]["auth"]["password"]
            elasticsearch_password = data["elasticsearch"]["security"][
                "elasticPassword"
            ]
            # rabbitmq_password = data["rabbitmq"]["auth"]["password"]
        domain = data["common-infra-bootstrap"]["global"]["domain"]
        # limits_enabled = str(data["global"]["limitsEnabled"]).lower()
    except KeyError as e:
        error_console.print(f"Key {e} not found in {filename}.")
        raise typer.Exit(1)

    useInternalServerUrl = "true"
    hide = True
    domain = Prompt.ask("Domain", default=domain)

    # limits_enabled = Prompt.ask(
    #    "limitsEnabled", choices=["true", "false"], default=limits_enabled
    # )
    # keycloak_admin_password = prompt(
    #    "Keycloak Password", password=hide, default=keycloak_admin_password
    # )
    if interactive:
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
            "useInternalServerUrl",
            choices=["true", "false"],
            default=useInternalServerUrl,
        )

    try:
        # Airflow
        data["airflow"]["externalDatabase"]["password"] = airflow_externaldb_password
        data["airflow"]["auth"]["password"] = airflow_password
        data["airflow"]["airflow-infra-bootstrap"]["domain"] = domain
        data["common-infra-bootstrap"]["global"]["domain"] = domain
        data["common-infra-bootstrap"]["airflow"]["auth"]["password"] = airflow_password
        data["common-infra-bootstrap"]["airflow"]["externalDatabase"][
            "password"
        ] = airflow_password

        # Elasticseach
        data["elasticsearch"]["security"]["elasticPassword"] = elasticsearch_password
        data["elasticsearch"]["elastic-infra-bootstrap"]["global"]["domain"] = domain
        data["elasticsearch"]["elastic-infra-bootstrap"]["elastic_bootstrap"][
            "elasticPassword"
        ] = elasticsearch_password

        # Minio
        # data["global"]["limitsEnabled"] = bool(limits_enabled)
        data["minio"]["auth"]["rootPassword"] = minio_password
        data["minio"]["minio-infra-bootstrap"]["global"]["domain"] = domain
        data["minio"]["minio-infra-bootstrap"]["minio"]["auth"][
            "rootPassword"
        ] = minio_password
        # data["minio"]["useInternalServerUrl"] = bool(use_internal_server_url)
        # data["keycloak"]["auth"]["adminPassword"] = keycloak_admin_password

        # postgresql
        data["postgresql"]["global"]["postgresql"]["auth"][
            "postgresPassword"
        ] = postgresql_password
        data["postgresql"]["postgres-infra-bootstrap"]["global"]["domain"] = domain
        data["postgresql"]["postgres-infra-bootstrap"]["postgresql"]["global"][
            "postgresql"
        ]["auth"]["postgresPassword"] = postgresql_password

        # common-infra-bootstrap
        data["common-infra-bootstrap"]["global"]["domain"] = domain
        data["common-infra-bootstrap"]["airflow"]["auth"]["password"] = airflow_password
        data["common-infra-bootstrap"]["airflow"]["externalDatabase"][
            "password"
        ] = airflow_externaldb_password

        # cimpl-bootstrap-rabbitmq
        data["cimpl-bootstrap-rabbitmq"]["rabbitmq"]["auth"][
            "password"
        ] = rabbitmq_password

        # OSDU Services values
        data["core-plus-crs-catalog-deploy"]["global"]["domain"] = domain
        data["core-plus-crs-conversion-deploy"]["global"]["domain"] = domain
        data["core-plus-dataset-deploy"]["global"]["domain"] = domain
        data["core-plus-entitlements-deploy"]["global"]["domain"] = domain
        data["core-plus-file-deploy"]["global"]["domain"] = domain
        data["core-plus-indexer-deploy"]["global"]["domain"] = domain
        data["core-plus-legal-deploy"]["global"]["domain"] = domain
        data["core-plus-notification-deploy"]["global"]["domain"] = domain
        data["core-plus-partition-deploy"]["global"]["domain"] = domain
        data["core-plus-policy-deploy"]["global"]["domain"] = domain
        data["core-plus-register-deploy"]["global"]["domain"] = domain
        data["core-plus-schema-deploy"]["global"]["domain"] = domain
        data["core-plus-search-deploy"]["global"]["domain"] = domain
        data["core-plus-storage-deploy"]["global"]["domain"] = domain
        data["core-plus-unit-deploy"]["global"]["domain"] = domain
        data["core-plus-wellbore-deploy"]["global"]["domain"] = domain
        data["core-plus-wellbore-worker-deploy"]["global"]["domain"] = domain
        data["core-plus-workflow-deploy"]["global"]["domain"] = domain
        data["core-plus-secret-deploy"]["global"]["domain"] = domain

    except KeyError as e:
        error_console.print(f"Key {e} not found in processing {filename}.")
        raise typer.Exit(1)

    if Confirm.ask("Save?", default=True):
        with open(filename, "w") as file:
            yaml = ruamel.yaml.YAML()
            yaml.dump(data, file)
            console.print(f"Updated: {filename}")

    # if Confirm.ask("Install?", default=True):
    #    output = helm_install()
    #    console.print(output)


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
        bool, typer.Option("--force", help="No confirmation prompt")
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
        bool, typer.Option("--force", help="No confirmation prompt")
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
        with console.status("Cleaning up remaining..."):
            console.print(cik8s.delete_item("secret"))
            console.print(cik8s.delete_item("pvc"))
            console.print(cik8s.delete_all(namespace=namespace))
            console.print(cik8s.delete_all(namespace=istio_namespace))
    else:
        raise typer.Abort()


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


@cli.command(rich_help_panel="CI Commands")
def install(
    version: Annotated[str, typer.Option(help="CImpl version")] = "0.27.0-local",
    source: Annotated[
        str, typer.Option(help="CImpl source")
    ] = "oci://us-central1-docker.pkg.dev/or2-msq-gnrg-osdu-mp-t1iylu/cimpl/helm/osdu-cimpl",
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
        bool, typer.Option("--quiet", help="Less output / for non-interactive use")
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
    force: Annotated[
        bool, typer.Option(help="Attempt to force install", hidden=True)
    ] = False,
    minikube: Annotated[
        bool,
        typer.Option(
            "--minikube/--kubernetes",
            "-m/-k",
            help="Deploy Minikube (in Docker) or existing kubernetes cluster",
        ),
    ] = True,
    arm: Annotated[
        bool,
        typer.Option(
            "--arm/--x86",
            help="Set CPU Arch ARM/x86 of Kubernetes Nodes. For use with -k",
        ),
    ] = False,
    debug: Annotated[bool, typer.Option(help="Debug", hidden=True)] = False,
):
    """
    Install CImpli using minikube or kubernetes cluster, install notebook and data load. :rocket:

    data-load-flag options:
    'dd-reference', 'partial-dd-reference', 'tno-volve-reference', 'all', 'skip'
    Leaving data-load-flag will cause install to prompt for value

    """

    if (
        minikube
        or "docker-desktop" in cik8s.get_current_valid_context()
        or "minikube" in cik8s.get_current_valid_context()
    ):
        """
        If using minikube or docker-desktop as target then let's use
        arch of machine to give hints as to what container build would run
        best for CImpl
        """
        arch = platform.machine()
        if arch == "arm64" or arch == "aarch64":
            console.print(":sparkles: Running on ARM architecture")
            arm = True
        else:
            console.print(":sparkles: Running on x86 architecture")

    start = time.time()
    if minikube:
        ciminikube.config_minikube(
            percent_memory=percent_memory,
            max_memory=max_memory,
            max_cpu=max_cpu,
            disk_size=disk_size,
        )
        ciminikube.minikube_start(force=force)

    if debug:
        input("Continue with istio?")

    if not check_istio() and not install_istio():
        error_console.print("Installation has failed")
        raise typer.Exit(1)

    if debug:
        input("Continue with install cimpl?")

    install_cimpl(version=version, source=source, arm=arm)

    if debug:
        input("Continue with update services?")
    update_services(debug=debug)

    if debug:
        input("Continue with check running?")
    if not check_running(entitlement_workaround=True, quiet=quiet):
        error_console.print("Installation has failed")
        raise typer.Exit(1)

    duration = time.time() - start
    duration_str = utils.convert_time(duration)
    console.print(
        f"CImpl installed in {duration_str}. Ready to install Notebook and Upload data"
    )

    if debug:
        input("Continue with check running?")
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
    console.print(f"Install command completed in {duration_str}")


def data_load(data_load_flag, data_source, data_version, wait_for_complete=True):
    load_work_products = False
    if data_load_flag and "skip" in data_load_flag:
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


@cli.command(rich_help_panel="CI Commands")
def check(
    all: Annotated[bool, typer.Option("--all", "-k", help="Additional checks")] = False,
    skip_docker_daemon: Annotated[
        bool, typer.Option("--skip-docker-daemon", help="Skip testing docker daemon")
    ] = False,
):
    """
    Install Preflight Check
    """
    console.print(f"Platform: {platform.platform()}")
    utils.cpu_info()
    preflight_checks(skip_docker_daemon=skip_docker_daemon)
    cimpl.check_hosts()
    if all:
        k8s_checks()


def preflight_checks(skip_docker_daemon=False):
    total_heap_required = 26
    MIN_CPU_CORES = 6
    with console.status("Checking Requirements..."):
        external_utils = [
            "docker",
            "minikube",
            "kubectl",
            "helm",
            "pip",
        ]
        for cmd in external_utils:
            cmd_path = shutil.which(cmd)
            if cmd_path:
                console.print(f":white_check_mark: {cmd} installed")
            else:
                error_console.print(f":x: {cmd} not installed or not found")

        if skip_docker_daemon:
            return

        # nprocs = utils.getconf_nprocs_online()
        nprocs = utils.cpu_count()
        if nprocs and nprocs >= MIN_CPU_CORES:
            console.print(f":white_check_mark: CPU Cores online: {nprocs} :thumbs_up:")
        else:
            error_console.print(f":x: Not enough CPU cores detected {nprocs}")

        ncpu = cidocker.docker_info_ncpu()
        if ncpu == 0:
            error_console.print(
                ":x: Error getting NCPU setting. Is the docker daemon running?"
            )
            raise typer.Exit(2)
        elif ncpu >= MIN_CPU_CORES:
            console.print(f":white_check_mark: Docker CPU Limit: {ncpu} :thumbs_up:")
        else:
            error_console.print(
                f":x: Docker CPU Limit too low. Not enough CPU given to docker {ncpu}"
            )
            console.print(
                f"Please increase to a min. {MIN_CPU_CORES}.\nIf you recently changed this value try restarting docker."
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


def k8s_checks():
    info = cik8s.cluster_info()
    if info.count("running") >= 2:
        console.print(":white_check_mark: Kubernetes cluster running :thumbs_up:")
    else:
        error_console.print(":x: Kubernetes may not be running:")
        print(info)
        raise typer.Exit(1)

    cores = cik8s.kube_allocatable_cpu()
    if cores >= 4:
        console.print(f":white_check_mark: Kubernetes CPU cores {cores} :thumbs_up:")
    else:
        error_console.print(f":x: Not enough CPU {cores} given to docker/kubernetes")
        raise typer.Exit(1)

    k8s_memory = cik8s.kube_allocatable_memory()
    if k8s_memory.endswith("Ki"):
        ki = int(k8s_memory.replace("Ki", ""))
        gb = ki / 1024 / 1024
        if gb >= 23.2:
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
