import typer
from rich.console import Console
import logging
from fabric import Connection
from typing_extensions import Annotated
from cibutler.shell import run_shell_command
import time

# gcloud compute config-ssh

logger = logging.getLogger(__name__)

console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

diag_cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_checks():
    """
    Google Cloud checks

    gcloud auth application-default login
    """
    # Add GCP specific checks here
    # For example, checking if gcloud is installed, if the user is authenticated, etc.
    try:
        import google.auth  # Ensure google-auth is installed

        credentials, project = google.auth.default()
        console.print(f"Authenticated to GCP project: {project}")
    except ImportError:
        error_console.print(
            ":x: google-auth package is not installed. Please install it."
        )
        raise typer.Exit(1)
    except Exception as e:
        error_console.print(f":x: Error during GCP checks: {e}")
        raise typer.Exit(1)
    console.print(":white_check_mark: GCP checks passed")


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def ssh(
    host: Annotated[str, typer.Argument(help="host", envvar="HOST")] = None,
    command: Annotated[str, typer.Option(help="command")] = "uname -s",
    hide: Annotated[bool, typer.Option(help="Hide output")] = True,
):
    """
    SSH into a remote host and run a command to check connectivity or run a command.

    Typically used after "gcloud compute config-ssh"
    """
    result = Connection(host).run(command, hide=hide)
    if result.ok:
        console.print(f"Connected to {host}")
        console.print(f"Remote: {result.stdout.strip()}")
        logger.info(f"Command: {command} output: {result.stdout.strip()}")
        return result.stdout.strip()
    else:
        error_console.print(f"Failed to connect to {host}: {result.stderr.strip()}")
        logger.error(f"Failed Command: {command} output: {result.stdout.strip()}")
        raise typer.Exit(1)


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_config_ssh():
    """
    Populate SSH config files with Host entries from each gcloud instance
    """
    run_shell_command("gcloud compute config-ssh")


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_service_account():
    """
    Get the current gcloud service account
    """
    run_shell_command('gcloud iam service-accounts  list --format "value(email)"')


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_instance_create(
    project: Annotated[str, typer.Argument(help="GCP Project", envvar="PROJECT")],
    service_account: Annotated[
        str, typer.Argument(help="Service Account", envvar="SERVICE_ACCOUNT")
    ],
    instance: Annotated[
        str, typer.Option(help="Instance Name", envvar="INSTANCE")
    ] = "instance-osdu",
    zone: Annotated[
        str, typer.Option(help="GCP Zone", envvar="ZONE")
    ] = "us-central1-b",
    series: Annotated[str, typer.Option(help="Instance Type", envvar="SERIES")] = "n2",
    cores: Annotated[int, typer.Option(help="Instance Cores", envvar="CORES")] = 6,
    gb: Annotated[
        int, typer.Option("--ram", help="Instance GB RAM", envvar="RAM")
    ] = 36,
):
    """
    Create a GCP VM with Ubuntu
    """
    vcpu = cores * 2
    ram = gb * 1024  # Convert GB to MB
    with console.status(
        f"Creating VM {instance} in project {project} in zone {zone}..."
    ):
        # --machine-type=e2-custom-6-32768 \
        run_shell_command(
            f"gcloud compute instances create {instance} \
    --project={project} \
    --zone={zone} \
    --description='OSDU CIButler Testing' \
    --machine-type={series}-custom-{vcpu}-{ram} \
    --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
    --metadata=enable-osconfig=TRUE \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --service-account={service_account} \
    --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/trace.append \
    --tags=http-server,https-server \
    --create-disk=auto-delete=yes,boot=yes,device-name={instance},image=projects/ubuntu-os-cloud/global/images/ubuntu-minimal-2504-plucky-amd64-v20250708,mode=rw,size=132,type=pd-balanced \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --labels=goog-ops-agent-policy=v2-x86-template-1-4-0,goog-ec-src=vm_add-gcloud \
    --reservation-affinity=any "
        )


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_list_instances(
    project: Annotated[str, typer.Argument(help="GCP Project", envvar="PROJECT")],
    zone: Annotated[
        str, typer.Option(help="GCP Zone", envvar="ZONE")
    ] = "us-central1-b",
):
    """
    List GCP VM instances in a project and zone
    """
    run_shell_command(
        f"gcloud compute instances list --project={project} --zones={zone}"
    )


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_instance_stop(
    instance: Annotated[str, typer.Argument(help="GCP Instance", envvar="INSTANCE")],
    zone: Annotated[
        str, typer.Option(help="GCP Zone", envvar="ZONE")
    ] = "us-central1-b",
):
    """
    Stop a GCP VM instance in zone
    """
    run_shell_command(f"gcloud compute instances stop {instance} --zone={zone}")


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_instance_start(
    instance: Annotated[str, typer.Argument(help="GCP Instance", envvar="INSTANCE")],
    zone: Annotated[
        str, typer.Option(help="GCP Zone", envvar="ZONE")
    ] = "us-central1-b",
):
    """
    Start a GCP VM instance in zone
    """
    run_shell_command(f"gcloud compute instances start {instance} --zone={zone}")


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_instance_delete(
    instance: Annotated[str, typer.Argument(help="GCP Instance", envvar="INSTANCE")],
    zone: Annotated[
        str, typer.Option(help="GCP Zone", envvar="ZONE")
    ] = "us-central1-b",
):
    """
    Delete a GCP VM instance in zone
    """
    run_shell_command(f"gcloud compute instances delete {instance} --zone={zone}")


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def cloud_install_ubuntu_minikube(
    host: Annotated[str, typer.Argument(help="host", envvar="HOST")] = None,
    hide: Annotated[bool, typer.Option(help="Hide output")] = False,
):
    """
    Install on remote ubuntu linux host via SSH with minikube
    """
    remote_user = ssh(command="whoami", host=host, hide=hide)
    start_time = time.time()
    with console.status(f"Installing on {host}..."):
        with Connection(host) as c:
            console.print(f"Installing on {host} as user {remote_user}")
            c.run("sudo apt-get update")
            c.run("sudo apt install -y curl gnome-terminal docker.io python3-pip pipx")
            c.run("sudo snap install helm --classic")
            c.run("sudo snap install kubectl --classic")
            c.run(
                "curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64"
            )
            c.run(
                "sudo install minikube-linux-amd64 /usr/local/bin/minikube && rm minikube-linux-amd64"
            )
            c.run(f"sudo usermod -aG docker {remote_user}")
            # c.run("sudo newgrp docker")
            c.run("pipx ensurepath")
            c.run("pipx install hostsman")
            c.run(
                "sudo .local/share/pipx/venvs/hostsman/bin/hostsman -i osdu.localhost:127.0.0.1 osdu.local:127.0.0.1 airflow.localhost:127.0.0.1 airflow.local:127.0.0.1 minio.localhost:127.0.0.1 minio.local:127.0.0.1 keycloak.localhost:127.0.0.1 keycloak.local:127.0.0.1"
            )
            c.run(
                'pipx install cibutler --index-url https://community.opengroup.org/api/v4/projects/1558/packages/pypi/simple --pip-args="--extra-index-url=https://community.opengroup.org/api/v4/projects/148/packages/pypi/simple"'
            )
            c.run(".local/bin/cibutler --version")

    elapsed_time = time.time() - start_time
    console.print(
        f":white_check_mark: Installation completed on {host} in {elapsed_time:.2f} seconds"
    )


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def cloud_install_ubuntu_k8s(
    host: Annotated[str, typer.Argument(help="host", envvar="HOST")] = None,
    hide: Annotated[bool, typer.Option(help="Hide output")] = False,
):
    """
    Install on remote ubuntu linux host via SSH with k8s
    """
    remote_user = ssh(command="whoami", host=host, hide=hide)
    start_time = time.time()
    with console.status(f"Installing on {host}..."):
        with Connection(host) as c:
            console.print(f"Installing on {host} as user {remote_user}")
            c.run("sudo apt-get update")
            c.run("sudo apt install -y curl python3-pip pipx")
            c.run("sudo snap install k8s --classic")
            c.run("sudo snap install helm --classic")
            c.run("pipx ensurepath")
            c.run("pipx install hostsman")
            c.run(
                "sudo .local/share/pipx/venvs/hostsman/bin/hostsman -i osdu.localhost:127.0.0.1 osdu.local:127.0.0.1 airflow.localhost:127.0.0.1 airflow.local:127.0.0.1 minio.localhost:127.0.0.1 minio.local:127.0.0.1 keycloak.localhost:127.0.0.1 keycloak.local:127.0.0.1"
            )
            c.run(
                'pipx install cibutler --index-url https://community.opengroup.org/api/v4/projects/1558/packages/pypi/simple --pip-args="--extra-index-url=https://community.opengroup.org/api/v4/projects/148/packages/pypi/simple"'
            )
            c.run(".local/bin/cibutler --version")
            c.run("sudo k8s bootstrap")
            c.run("sudo k8s status")

    elapsed_time = time.time() - start_time
    console.print(
        f":white_check_mark: Installation completed on {host} in {elapsed_time:.2f} seconds"
    )


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def cloud_install_ubuntu_microk8s(
    host: Annotated[str, typer.Argument(help="host", envvar="HOST")] = None,
    hide: Annotated[bool, typer.Option(help="Hide output")] = False,
):
    """
    Install on remote ubuntu linux host via SSH with MicroK8s
    """
    remote_user = ssh(command="whoami", host=host, hide=hide)
    start_time = time.time()
    with console.status(f"Installing on {host}..."):
        with Connection(host) as c:
            console.print(f"Installing on {host} as user {remote_user}")
            c.run("sudo apt-get update")
            c.run("sudo apt install -y curl python3-pip pipx")
            c.run("sudo snap install microk8s --classic")
            c.run("sudo snap install helm --classic")
            c.run("pipx ensurepath")
            c.run("pipx install hostsman")
            c.run(
                "sudo .local/share/pipx/venvs/hostsman/bin/hostsman -i osdu.localhost:127.0.0.1 osdu.local:127.0.0.1 airflow.localhost:127.0.0.1 airflow.local:127.0.0.1 minio.localhost:127.0.0.1 minio.local:127.0.0.1 keycloak.localhost:127.0.0.1 keycloak.local:127.0.0.1"
            )
            c.run(
                'pipx install cibutler --index-url https://community.opengroup.org/api/v4/projects/1558/packages/pypi/simple --pip-args="--extra-index-url=https://community.opengroup.org/api/v4/projects/148/packages/pypi/simple"'
            )
            c.run(".local/bin/cibutler --version")
            c.run("sudo microk8s enable dns")
            c.run("sudo microk8s enable storage")
            c.run(f"sudo usermod -a -G microk8s {remote_user}")
            c.run("sudo snap install kubectl --classic")
            c.run("mkdir -p ~/.kube")
            c.run("cd ~/.kube && microk8s config > config")

    # c.run("sudo ufw allow in on cni0 && sudo ufw allow out on cni0")
    # c.run("sudo ufw default allow routed")
    elapsed_time = time.time() - start_time
    console.print(
        f":white_check_mark: Installation completed on {host} in {elapsed_time:.2f} seconds"
    )


if __name__ == "__main__":
    diag_cli()
