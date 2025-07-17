from subprocess import call
import os
import typer
from rich.console import Console
import rich.progress
import ruamel.yaml
import platform
import time
import subprocess
import inquirer
import shlex
import base64
import logging
from typing_extensions import Annotated
import cibutler.cik8s as cik8s
import cibutler.utils as utils
from cibutler.shell import run_shell_command

logger = logging.getLogger(__name__)

console = Console()
error_console = Console(stderr=True, style="bold red")

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
        else:
            error_console.print(f":x: {host} not in hosts file")


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands")
def cpu():
    """
    Display CPU info
    """
    console.print(utils.cpu_info())
    console.print(f"Logic cores: {os.cpu_count()}")
    if "Darwin" in platform.system():
        console.print(f"Performance Cores: {utils.macos_performance_cores()}")


def install_cimpl(version: str, source: str, chart: str = "osdu-cimpl"):
    """
    Install CImpl OCI registry or local source
    """

    rabbitmq_password = utils.random_password()
    redis_password = utils.random_password()
    core_unit_deploy_enabled = "false"

    console.print(f"Using RabbitMQ password: {rabbitmq_password}")
    console.print(f"Using Redis password: {redis_password}")
    console.print(f"Core Unit Deploy Enabled: {core_unit_deploy_enabled}")

    console.log(f":pushpin: Requested install version {version} from {source}...")
    if source.startswith("oci://"):
        # OCI registry source
        logger.info(f"Using OCI registry source {source} for CImpl {version}")
        console.log(f":fire: Using OCI registry source {source} for CImpl {version}")
        run_shell_command(
            f"helm upgrade --install --set rabbitmq.auth.password={rabbitmq_password} --set global.redis.password={redis_password} --set core_unit_deploy.enabled={core_unit_deploy_enabled} {chart} {source} --version {version}"
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
    console.print(":fire: Installing Notebook...")
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


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands")
def check_running(
    sleep: int = 120,
    bootstrap_sleep: int = 30,
    max: int = 50,
    quiet: bool = False,
    entitlement_workaround: bool = False,
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
        if pods_not_ready:
            # If keycloak and partition bootstrap completed, restart the entitlements.
            # Hopefully this will get fixed in the future
            if (
                entitlement_workaround
                and "partition-bootstrap" in pods_not_ready
                and "keycloak-bootstrap" in pods_not_ready
            ):
                console.print(":fire: [cyan]Restarting entitlements...[/cyan]")
                # kubectl rollout restart deploy entitlements > /dev/null
                call(
                    ["kubectl", "rollout", "restart", "deploy", "entitlements"],
                    stdout=subprocess.DEVNULL,
                )  # nosec
                # kubectl rollout restart deploy entitlements-bootstrap > /dev/null
                call(
                    [
                        "kubectl",
                        "rollout",
                        "restart",
                        "deploy",
                        "entitlements-bootstrap",
                    ],
                    stdout=subprocess.DEVNULL,
                )  # nosec

            if flag.exit():
                break

            # if running over max time
            if duration > (60 * max):
                error_console.print(
                    f"There seems to be an issue with `{pods_not_ready}`."
                )
                console.print(
                    "Please get the logs of crashing pod with 'kubectl logs <Name-of-the-pod>"
                )
                break

            console.print()
            count = len(pods_not_ready.strip().split(" "))
            duration_str = utils.convert_time(duration)
            console.print(
                f":person_running: Pods not yet ready: {count}, elapsed: {duration_str}"
            )
            for _ in rich.progress.track(
                range(sleep),
                transient=True,
                description=f"The status will be updated every {sleep} seconds. Please, do not interrupt script execution.",
            ):
                time.sleep(1)
        else:
            console.print(":thumbs_up: pods ready")
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
                console.print(f":thumbs_up: {bootstrap} ready")
                logger.info(f"{bootstrap} is ready")
                running = True
                break
            else:
                console.print(
                    "Bootstrap default set of schemas is still in progress..."
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
            error_console.print("Install failed. Too many errors")
            logger.error("Install failed. Too many errors")
            return False

    duration = time.time() - start
    if duration > 2:
        duration_str = utils.convert_time(duration)
        console.print(f"CImpl bootstrap completed {duration_str}.")
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
                console.print(":thumbs_up: reference data bootstrapped.")
                logger.info("reference data bootstrapped.")
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


def get_data_load_option():
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
        console.print(answers["data_load_flag"])
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
