from subprocess import call
import os
import typer
import rich.progress
import ruamel.yaml
import platform
import time
import subprocess
import inquirer
import shlex
import base64
import logging
from rich.panel import Panel
from typing_extensions import Annotated
import cibutler.cik8s as cik8s
import cibutler.utils as utils
from cibutler.shell import run_shell_command
from cibutler.common import console, error_console

logger = logging.getLogger(__name__)

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

diag_cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands")
def check_hosts():
    """
    Check hosts file
    """
    good = True
    required = [
        "osdu.localhost",
        "osdu.local",
        "airflow.localhost",
        "minio.localhost",
        "keycloak.localhost",
    ]
    for host in required:
        if utils.resolvehostname(host):
            console.print(f":white_check_mark: {host} resolves")
            logger.info(f"{host} resolves")
        else:
            error_console.print(f":x: {host} not in hosts file")
            logger.error(f"{host} not in hosts file")
            good = False
    return good


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands")
def cpu():
    """
    Display CPU info
    """
    if "Darwin" in platform.system():
        console.print(
            f"CPU: {utils.cpu_info()} Logic cores: {os.cpu_count()} Performance Cores: {utils.macos_performance_cores()}"
        )
        logger.info(
            f"CPU: {utils.cpu_info()} Logic cores: {os.cpu_count()} Performance Cores: {utils.macos_performance_cores()}"
        )
    else:
        console.print(f"CPU: {utils.cpu_info()} Logic cores: {os.cpu_count()}")
        logger.info(f"CPU: {utils.cpu_info()} Logic cores: {os.cpu_count()}")


def install_cimpl(
    version: str,
    source: str,
    chart: str = "osdu-cimpl",
    configured_options: dict = None,
):
    """
    Install CImpl OCI registry or local source
    """

    rabbitmq_password = configured_options.get(
        "rabbitmq_password", utils.random_password()
    )
    redis_password = configured_options.get("redis_password", utils.random_password())
    osdu_services = configured_options.get("osdu_services")

    unit_enabled = str("Unit" in osdu_services).lower()
    crs_catalog_enabled = str("Crs-catalog" in osdu_services).lower()
    crs_converter_enabled = str("Crs-converter" in osdu_services).lower()
    policy_enabled = str("Policy" in osdu_services).lower()

    console.print(f"Using RabbitMQ password: {rabbitmq_password}")
    console.print(f"Using Redis password: {redis_password}")
    logger.debug(f"Using RabbitMQ password: {rabbitmq_password}")
    logger.debug(f"Using Redis password: {redis_password}")
    console.log(f"Core Unit Deploy Enabled: {unit_enabled}")
    logger.info(f"Core Unit Deploy Enabled: {unit_enabled}")
    console.log(f"Core CRS Catalog Deploy Enabled: {crs_catalog_enabled}")
    logger.info(f"Core CRS Catalog Deploy Enabled: {crs_catalog_enabled}")
    console.log(f"Core CRS Converter Deploy Enabled: {crs_converter_enabled}")
    logger.info(f"Core CRS Converter Deploy Enabled: {crs_converter_enabled}")
    console.log(f"Core Policy Deploy Enabled: {policy_enabled}")
    logger.info(f"Core Policy Deploy Enabled: {policy_enabled}")

    console.log(f":pushpin: Requested install version {version} from {source}...")

    if source.startswith("oci://"):
        # OCI registry source
        logger.info(f"Using OCI registry source {source} for CImpl {version}")
        console.log(f":fire: Using OCI registry source {source} for CImpl {version}")

        if version.startswith("0.27."):
            run_shell_command(
                f"helm upgrade --install \
            --set rabbitmq.auth.password={rabbitmq_password} \
            --set global.redis.password={redis_password} \
            {chart} {source} --version {version}"
            )
        else:
            run_shell_command(
                f"helm upgrade --install \
            --set rabbitmq.auth.password={rabbitmq_password} \
            --set global.redis.password={redis_password} \
            --set core_unit_deploy.enabled={unit_enabled} \
            --set core_partition_deploy.data.policyServiceEnabled={policy_enabled} \
            --set core_policy_deploy.enabled={policy_enabled} \
            --set core_crs_catalog_deploy.enabled={crs_catalog_enabled} \
            --set core-crs-catalog-deploy.enabled={crs_catalog_enabled} \
            --set core_crs_converter_deploy.enabled={crs_converter_enabled} \
            --set core-crs-converter-deploy.enabled={crs_converter_enabled} \
            {chart} {source} --version {version}"
            )
    else:
        # Local source
        logger.info(f"Using local source {source} for CImpl")
        console.log(f":fire: Using local source {source} for CImpl")
        run_shell_command(f"helm upgrade --install {chart} {source}")

    time.sleep(1)


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands")
def update_services(
    debug: Annotated[bool, typer.Option(help="Run with Debug")] = False,
    add_host: Annotated[str, typer.Option(help="Add additional hosts")] = None,
):
    """
    Update service virtual services - add additional hosts, etc
    """

    svcs = cik8s.kubectl_get(opt="vs")
    with console.status("Updating services..."):
        for line in svcs.splitlines():
            vsvc = line.split()[0]
            if "cimpl" not in vsvc and "NAME" not in vsvc:
                filename = f"{vsvc}.yaml"
                console.print(f"{vsvc} :detective: ", end="")
                with open(filename, "w") as outfile:
                    call(
                        ["kubectl", "get", "virtualservice", vsvc, "-o", "yaml"],
                        stdout=outfile,
                    )  # nosec

                try:
                    with open(filename, "r") as file:
                        yaml = ruamel.yaml.YAML()
                        data = yaml.load(file)
                        if add_host:
                            data["spec"]["hosts"] = [
                                "osdu.localhost",
                                "osdu.cimpl",
                                add_host,
                            ]
                        else:
                            data["spec"]["hosts"] = ["osdu.localhost", "osdu.cimpl"]
                        console.print(":wrench:", end="")
                except FileNotFoundError:
                    error_console.print(f"{filename} was not saved")
                    raise typer.Exit(1)

                try:
                    with open(filename, "w") as file:
                        yaml.dump(data, file)
                        console.print(f":hammer_and_wrench: {filename}")
                except FileNotFoundError:
                    error_console.print(f"{filename} unable to open")
                    raise typer.Exit(1)

                call(
                    ["kubectl", "delete", "virtualservice", vsvc],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                )  # nosec
                call(
                    ["kubectl", "apply", "-f", filename],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                )  # nosec

                if not debug:
                    os.remove(filename)

        call(
            ["kubectl", "delete", "ra", "--all"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )  # nosec
        call(
            ["kubectl", "delete", "authorizationpolicy", "entitlements-jwt-policy"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )  # nosec


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands", name="notebook")
def notebook(
    notebook: str = "oci://us-central1-docker.pkg.dev/or2-msq-gnrg-osdu-mp-t1iylu/cimpl/helm/cimpl-notebook",
    notebook_version: str = "0.0.1",
    token: bool = False,
):
    """
    Install/reinstall notebook
    """
    if token:
        console.print(get_notebook_token())
    else:
        helm_install_notebook(notebook_source=notebook, version=notebook_version)


def helm_install_notebook(notebook_source: str, version: str):
    with console.status("Getting ingress..."):
        ingress_ip = cik8s.get_ingress_ip()
    console.log(":fire: Installing Notebook...")
    logger.info(f"Installing Notebook... {notebook_source} {version} {ingress_ip}")
    run_shell_command(
        f"helm upgrade --install cimpl-notebook {notebook_source} --version {version} --set conf.ingressIP={ingress_ip}"
    )


def readyandavailable(data):
    return (
        "readyReplicas" in data
        and data["readyReplicas"]
        and "availableReplicas" in data
        and data["availableReplicas"]
    )


def restart_entitlements():
    logger.info(
        "Restarting entitlements (deployment and bootstrap) due to keycloak and partition-bootstrap not ready"
    )
    console.print(
        ":fire: [cyan]Restarting entitlements (deployment and bootstrap)...[/cyan]"
    )
    # kubectl rollout restart deploy entitlements > /dev/null
    call(
        ["kubectl", "rollout", "restart", "deploy", "entitlements"],
        stdout=subprocess.DEVNULL,
    )  # nosec
    # kubectl rollout restart deploy entitlements-bootstrap > /dev/null
    call(
        ["kubectl", "rollout", "restart", "deploy", "entitlements-bootstrap"],
        stdout=subprocess.DEVNULL,
    )  # nosec


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands", hidden=True)
def display_error_msg(errors: int = 0, version: str = "unknown", minikube: bool = False, source: str = "unknown"):
    output = f"""
    Your system may still be usable, but these pods are not ready.
    Notebook and Data loading will not be run. You can run them manually
    however.

    This may be an issue with helm chart, the container image, or the OSDU
    service itself either way CI Butler is not currently able to handle this
    particular situation.

    Please review the logs of crashing pod with:
    [code]kubectl logs <Name-of-the-pod>[/code]

    If you want to package logs and diagnostics, you can run:
    [code]cibutler diag inspect[/code]

    For troubleshooting tips:
        https://osdu.pages.opengroup.org/ui/cibutler/troubleshooting/
    You can also raise an issue at:
        https://community.opengroup.org/osdu/ui/cibutler/-/issues

    version: {version} Deployment: {'Minikube' if minikube else 'Kubernetes'}
    source: {source}
    """

    border_style = "yellow"
    if errors > 3:
        logger.error(f"There were {errors} errors during install.")
        border_style = "red"
        output = f"""
    :x: [bold red]There were {errors} errors during install.[/bold red]
        {output}
    """

    console.print(
        Panel(
            output,
            border_style=border_style,
            box=rich.box.SQUARE,
            expand=True,
            title="[cyan]CI Butler OSDU Install Failure [/cyan]",
        )
    )


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands")
def check_running(
    version: str,
    minikube: bool,
    sleep: int = 120,
    bootstrap_sleep: int = 30,
    max_wait: int = 50,
    quiet: bool = False,
    entitlement_workaround: bool = False,
    source: str = "unknown",
):
    """
    Check if CImpl is running (and make simple corrections)
    """
    start = time.time()
    running = False
    errors = 0

    flag = utils.GracefulExiter()
    while True:
        if not quiet:
            console.clear()
            call(["kubectl", "get", "po"])  # nosec

        pods_not_ready = cik8s.get_pods_not_running()
        duration = time.time() - start
        duration_str = utils.convert_time(duration)
        if pods_not_ready:
            # If keycloak and partition bootstrap completed, restart the entitlements.
            # Hopefully this will get fixed in the future
            if (
                entitlement_workaround
                and "partition-bootstrap" in pods_not_ready
                and "keycloak-bootstrap" in pods_not_ready
            ):
                restart_entitlements()

            if flag.exit():
                break

            # if running over max time
            if duration > (60 * max_wait):
                error_console.log(
                    f"There seems to be an issue with `{pods_not_ready}`."
                )
                logger.error(
                    f"There seems to be an issue with `{pods_not_ready}`. Exiting after {max_wait} minutes. {duration_str} elapsed."
                )
                display_error_msg(errors, version=version, minikube=minikube)
                break

            console.print()
            count = len(pods_not_ready.strip().split(" "))
            console.print(
                f":person_running: Pods not ready: {count}, elapsed: {duration_str}, version: {version}, {'Minikube' if minikube else 'Kubernetes'}",
            )
            logger.info(
                f":person_running: Pods not ready: {count}, elapsed: {duration_str}, version: {version}, {'Minikube' if minikube else 'Kubernetes'}",
            )
            logger.info(f"Pods not ready: {pods_not_ready}")
            for _ in rich.progress.track(
                range(sleep),
                transient=True,
                description=f"The status will be updated every {sleep} seconds. Please, do not interrupt script execution.",
            ):
                time.sleep(1)
        else:
            console.log(":thumbs_up: pods ready")
            logger.info("Pods ready")
            bootstrap = "schema-bootstrap"
            data = cik8s.get_deployment_status(bootstrap)
            if data is None:
                error_console.print(
                    f":x: Error: Unable to determine {bootstrap} status"
                )
                logger.error(
                    f"Unable to determine {bootstrap} status. Check if the deployment exists."
                )
                errors += 1
                time.sleep(1)
            elif readyandavailable(data):
                console.log(f":thumbs_up: {bootstrap} ready")
                logger.info(f"{bootstrap} is ready")
                running = True
                break
            else:
                console.log(
                    f"Bootstrap default set of schemas is still in progress...{duration_str}"
                )
                if quiet:
                    time.sleep(bootstrap_sleep)
                else:
                    with console.status(
                        f"The status will be updated every {bootstrap_sleep} seconds. Please, do not interrupt script execution.",
                        spinner="aesthetic",
                    ):
                        time.sleep(bootstrap_sleep)

        if errors > 3:
            error_console.log("Install failed. Too many errors")
            display_error_msg(errors, version=version, minikube=minikube)
            logger.error(f"Install failed. Too many errors: {errors}")
            return False

    duration = time.time() - start
    if duration > 2:
        duration_str = utils.convert_time(duration)
        console.log(f"CImpl bootstrap completed {duration_str}.")
        logger.info(f"CImpl bootstrap completed {duration_str}.")
    return running


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands")
def bootstrap_upload_data(
    data_load_flag: str,
    source: str,
    version: str,
    partition: str = "osdu",
    load_work_products: bool = False,
    service_account_name: str = "bootstrap-sa",
    wait_for_complete: bool = True,
    bootstrap_data_reference: str = "bootstrap-data-reference",
    bootstrap_data_legal: str = "bootstrap-data-legal",
    sleep: int = 30,
):
    """
    Bootstrap data upload process into OSDU
    """
    console.log(f":fire: Starting uploading data: {data_load_flag}... {version}")
    logger.info(f"Starting uploading data: {data_load_flag}... {version}")

    run_shell_command(
        f'helm upgrade --install bootstrap-data-deploy {source}\
    --version {version} \
    --set global.dataPartitionId="{partition}" \
    --set global.onPremEnabled=true \
    --set global.deployWorkproducts={load_work_products} \
    --set data.bootstrapReferenceFlag="{data_load_flag}" \
    --set data.bootstrapServiceAccountName="{service_account_name}"'
    )

    console.log(f":fire: Updating deployments... {bootstrap_data_reference}")
    logger.info(f"Updating deployments... {bootstrap_data_reference}")
    scale_deploy(bootstrap_data_reference)
    # scale_deploy("bootstrap-data-workproduct")

    while True:
        status = cik8s.get_deployment_status(bootstrap_data_legal)
        if "readyReplicas" in status and status["readyReplicas"]:
            console.log(":thumbs_up: Legal data bootstrapped.")
            logger.info("Legal data bootstrapped.")
            break
        else:
            with console.status("Waiting for default legal tag"):
                time.sleep(sleep)

    console.log(":fire: Starting data load process...")
    logger.info("Starting data load process...")
    scale_deploy(bootstrap_data_reference, replicas=1)
    start = time.time()
    if wait_for_complete:
        while True:
            status = cik8s.get_deployment_status(bootstrap_data_reference)
            if "readyReplicas" in status and status["readyReplicas"]:
                console.log(
                    f":thumbs_up: reference data bootstrapped {bootstrap_data_reference}."
                )
                logger.info(
                    f"reference data bootstrapped {bootstrap_data_reference} {data_load_flag}."
                )
                break
            else:
                duration = time.time() - start
                duration_str = utils.convert_time(duration)
                with console.status(
                    f"Data reference load ({data_load_flag}) running within the cluster {duration_str}"
                ):
                    time.sleep(sleep)

        duration = time.time() - start
        duration_str = utils.convert_time(duration)
        console.log(
            f"Data loading process ({data_load_flag}) completed. {duration_str}"
        )
        logger.info(
            f"Data loading process ({data_load_flag}) completed. {duration_str}"
        )
    else:
        msg = """
        Data loading process started. It is performed inside the minikube cluster.
        You can check the status with command 'kubectl get po | grep bootstrap-data'
        The numbers '1/1' in READY column means that data loading process finished.
        """
        console.print(msg)

    # scale_deploy("bootstrap-data-workproduct", replicas=1)
    # if load_work_products:
    #    scale_deploy("bootstrap-data-workproduct")


def scale_deploy(deployment: str, replicas: bool = 0):
    run_shell_command(f"kubectl scale deploy {deployment} --replicas {replicas}")


def data_load_callback(option: str):
    options = [
        "dd-reference",
        "partial-dd-reference",
        "tno-volve-reference",
        "all",
        "skip",
        None,
    ]
    if option not in options:
        raise typer.BadParameter(
            f"Bad data load flag {option}. Allowed values: {options}"
        )
    return option


def get_data_load_option(defaults: bool = False):
    if defaults:
        return "dd-reference"

    options = [
        "dd-reference",
        "partial-dd-reference",
        "tno-volve-reference",
        "all",
        "skip",
    ]
    title = """
            dd-reference - upload only part of reference data (10000 records). Estimated time: ~10min,\n
            partial-dd-reference - upload all for reference data. Estimated time: ~30min,
            tno-volve-reference - upload all TNO data. Estimated time: ~1h 15min,
            all - upload reference and workproduct data Estimated time: ~4h,

        Select which data load option:
        """

    console.print(title)
    questions = [
        inquirer.List(
            "data_load_flag",
            message="What data would you like to load?",
            choices=options,
        ),
    ]
    answers = inquirer.prompt(questions)
    if "skip" in answers["data_load_flag"]:
        console.print("skipping")
        return None
    else:
        console.print("You selected: ", answers["data_load_flag"])
        return answers["data_load_flag"]


def get_keycloak_client_secret():
    """
    Get client secret from keycloak secrets
    """
    cmd = 'kubectl get secret keycloak-bootstrap-secret -o jsonpath="{.data.KEYCLOAK_OSDU_ADMIN_SECRET}"'  # nosec
    args = shlex.split(cmd)
    output = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
    return base64.b64decode(output.decode("ascii").strip()).decode()


def get_keycloak_admin_password():
    """
    Get admin password from keycloak secrets
    """
    cmd = 'kubectl get secret keycloak-bootstrap-secret -o jsonpath="{.data.KEYCLOAK_ADMIN_PASSWORD}"'  # nosec
    args = shlex.split(cmd)
    output = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
    return base64.b64decode(output.decode("ascii").strip()).decode()


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands")
def client_secret():
    """
    Display Client Secret from keycloak secrets
    """
    console.print(get_keycloak_client_secret())


def get_notebook_pod():
    """
    Get pod name of notebook
    """
    cmd = "kubectl get --no-headers pods -l app=cimpl-notebook"  # nosec
    args = shlex.split(cmd)
    output = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
    return output.decode("ascii").strip().split()[0]


def get_notebook_token():
    """
    Get token from running notebook pod
    """
    log = get_notebook_log()
    for line in log.split("\n"):
        if "127.0.0.1" in line and "token" in line:
            return line.split("?")[1]


def get_notebook_log():
    """
    Get log from running notebook pod
    """
    pod = get_notebook_pod()
    cmd = f"kubectl logs {pod}"  # nosec
    args = shlex.split(cmd)
    output = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
    return output.decode("ascii").strip()


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands")
def post_message(
    notebook_base_url: str = "http://notebook.localhost/notebooks/cimpl_notebook.ipynb",
    hostname: str = "osdu.localhost",
    client_id: str = "osdu-admin",
):
    """
    Display post install message
    """
    client_secret = get_keycloak_client_secret()
    admin_password = get_keycloak_admin_password()
    notebook_token = get_notebook_token()
    msg = f"""
    Airflow is available via: http://airflow.localhost/
    Keycloak is available via: http://keycloak.localhost/admin/
    MinIO is available via: http://minio.localhost/
    [green]Password for Airflow/Keycloak/Minio[/green]: {admin_password}

    [bold]OSDU Services Endpoints[/bold]:
    Config:           http://{hostname}/api/config/v1/info
    CRS-Catalog:      http://{hostname}/api/crs/catalog/v2/info
    CRS-Conversion:   http://{hostname}/api/crs/converter/v2/info
    Dataset:          http://{hostname}/api/dataset/v1/info
    Entitlements:     http://{hostname}/api/entitlements/v2/info
    File:             http://{hostname}/api/file/v2/info
    Indexer:          http://{hostname}/api/indexer/v2/info
    Legal:            http://{hostname}/api/legal/v1/info
    Notification:     http://{hostname}/api/notification/v1/info
    Partition:        http://{hostname}/api/partition/v1/info
    Register:         http://{hostname}/api/register/v1/info
    Schema:           http://{hostname}/api/schema-service/v1/info
    Search:           http://{hostname}/api/search/v2/info
    Secret:           http://{hostname}/api/secret/v1/info
    Storage:          http://{hostname}/api/storage/v2/info
    Wellbore DDMS:    http://{hostname}/api/os-wellbore-ddms/ddms/v2/about
    Workflow:         http://{hostname}/api/workflow/v1/info

    [bold]To access the OSDU APIs use credentials[/bold]:
    [green]Client ID[/green]: {client_id}
    [green]Client Secret[/green]: {client_secret}

    Run [code]minikube tunnel[/code] to access the services in minikube. Password is needed
    The link to Jupyter Notebook: {notebook_base_url}?{notebook_token}
    """
    console.print(msg)


if __name__ == "__main__":
    cli()
