import typer
from rich.console import Console
import logging
from fabric import Connection
from typing_extensions import Annotated
from cibutler.shell import run_shell_command
import subprocess
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
    # Add GC specific checks here
    # For example, checking if gcloud is installed, if the user is authenticated, etc.
    try:
        import google.auth  # Ensure google-auth is installed

        credentials, project = google.auth.default()
        console.print(f"Authenticated to GC project: {project}")
    except ImportError:
        error_console.print(
            ":x: google-auth package is not installed. Please install it."
        )
        raise typer.Exit(1)
    except Exception as e:
        error_console.print(f":x: Error during GC checks: {e}")
        raise typer.Exit(1)
    console.print(":white_check_mark: GC checks passed")


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def ssh(
    host: Annotated[str, typer.Argument(help="host", envvar="HOST")] = None,
    command: Annotated[str, typer.Option(help="command")] = "uname -s",
    hide: Annotated[bool, typer.Option(help="Hide output")] = True,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    SSH into a remote host and run a command to check connectivity or run a command.

    Typically used after "gcloud compute config-ssh"
    """
    result = Connection(host).run(command, hide=hide)
    if result.ok:
        if verbose:
            console.log(f"Connected to {host}")
            console.log(f"Remote: {result.stdout.strip()}")
        else:
            print(result.stdout.strip())
        logger.info(f"Command: {command} output: {result.stdout.strip()}")
        return result.stdout.strip()
    else:
        error_console.print(f"Failed to connect to {host}: {result.stderr.strip()}")
        logger.error(f"Failed Command: {command} output: {result.stdout.strip()}")
        raise typer.Exit(1)


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_config_ssh(
    host: Annotated[str, typer.Option(help="host", envvar="HOST")] = None,
    accept_new: Annotated[bool, typer.Option(help="accept ssh key")] = False,
):
    """
    Populate SSH config files with Host entries from each gcloud instance
    """
    run_shell_command("gcloud compute config-ssh")
    if accept_new:
        run_shell_command(f"ssh -o StrictHostKeyChecking=accept-new {host} uname")


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_ssh(
    instance: Annotated[
        str, typer.Option(help="Instance Name", envvar="INSTANCE")
    ] = "instance-osdu",
    zone: Annotated[str, typer.Option(help="GC Zone", envvar="ZONE")] = "us-central1-b",
):
    """
    gcloud ssh with tunnel for kubernetes
    """
    run_shell_command(
        f"gcloud compute ssh {instance} --zone {zone} --ssh-flag='-o ServerAliveInterval=60 -L 16443:localhost:16443'"
    )


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_service_account():
    """
    Get the current gcloud service account
    """
    run_shell_command('gcloud iam service-accounts  list --format "value(email)"')


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_instance_create(
    project: Annotated[str, typer.Argument(help="GC Project", envvar="PROJECT")],
    service_account: Annotated[
        str, typer.Argument(help="Service Account", envvar="SERVICE_ACCOUNT")
    ],
    instance: Annotated[
        str, typer.Option(help="Instance Name", envvar="INSTANCE")
    ] = "instance-osdu",
    zone: Annotated[str, typer.Option(help="GC Zone", envvar="ZONE")] = "us-central1-b",
    series: Annotated[str, typer.Option(help="Instance Type", envvar="SERIES")] = "n2",
    cores: Annotated[int, typer.Option(help="Instance Cores", envvar="CORES")] = 6,
    gb: Annotated[
        int, typer.Option("--ram", help="Instance GB RAM", envvar="RAM")
    ] = 36,
    diskgb: Annotated[int, typer.Option("--disk", help="Disk GB", envvar="DISK")] = 132,
    image: Annotated[
        str, typer.Option(help="Image Name", envvar="IMAGE")
    ] = "projects/ubuntu-os-cloud/global/images/ubuntu-minimal-2504-plucky-amd64-v20250708",
):
    """
    Create a GC VM, by default Ubuntu

    Optionally you can specify the image, series, cores, disk and RAM.

    For example:
    image=projects/rocky-linux-cloud/global/images/rocky-linux-9-optimized-gcp-v20250709
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
    --create-disk=auto-delete=yes,boot=yes,device-name={instance},image={image},mode=rw,size={diskgb},type=pd-balanced \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --labels=goog-ops-agent-policy=v2-x86-template-1-4-0,goog-ec-src=vm_add-gcloud \
    --reservation-affinity=any "
        )


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_list_instances(
    project: Annotated[str, typer.Argument(help="GC Project", envvar="PROJECT")],
    zone: Annotated[str, typer.Option(help="GC Zone", envvar="ZONE")] = "us-central1-b",
):
    """
    List GC VM instances in a project and zone
    """
    run_shell_command(
        f"gcloud compute instances list --project={project} --zones={zone}"
    )


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_instance_stop(
    instance: Annotated[str, typer.Argument(help="GC Instance", envvar="INSTANCE")],
    zone: Annotated[str, typer.Option(help="GC Zone", envvar="ZONE")] = "us-central1-b",
):
    """
    Stop a GC VM instance in zone
    """
    run_shell_command(f"gcloud compute instances stop {instance} --zone={zone}")


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_compute_images_list(
    filter: Annotated[
        str, typer.Option(help="Filter for images", envvar="FILTER")
    ] = "",
):
    """
    List GC VM images in a project with an optional filter
    """
    filter_option = f"--filter={filter}" if filter else ""
    output = subprocess.run(
        [
            "gcloud",
            "compute",
            "images",
            "list",
            "--uri",
            "--format",
            "json",
            filter_option,
        ],
        capture_output=True,
        check=True,
    )
    console.print(output.stdout.decode("utf-8"))
    return output.stdout.decode("utf-8")


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_compute_images(
    prefix: Annotated[
        str, typer.Option(help="Image prefix")
    ] = "https://www.googleapis.com/compute/v1/",
):
    """
    List GC VM images of ubuntu or rocky linux 9
    """
    image_list = gcloud_compute_images_list(
        filter="(name~ubuntu-minimal OR name~rocky-linux-9-optimized-gcp) AND (status=READY) AND NOT name~nvidia"  # noqa: E501
    )
    for image in image_list.splitlines():
        image = image.strip()
        image_name = image.removeprefix(prefix)
        console.print(f"Image: {image_name}")


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_instance_start(
    instance: Annotated[str, typer.Argument(help="GC Instance", envvar="INSTANCE")],
    zone: Annotated[str, typer.Option(help="GC Zone", envvar="ZONE")] = "us-central1-b",
):
    """
    Start a GC VM instance in zone
    """
    run_shell_command(f"gcloud compute instances start {instance} --zone={zone}")


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_instance_delete(
    instance: Annotated[str, typer.Argument(help="GC Instance", envvar="INSTANCE")],
    zone: Annotated[str, typer.Option(help="GC Zone", envvar="ZONE")] = "us-central1-b",
    force: Annotated[
        bool,
        typer.Option(
            "--force", "--yes", "--quiet", "-y", help="No confirmation prompt"
        ),
    ] = False,
):
    """
    Delete a GC VM instance in zone
    """
    if force:
        run_shell_command(
            f"gcloud compute instances delete {instance} --zone={zone} --delete-disks=all --quiet"
        )
    else:
        run_shell_command(
            f"gcloud compute instances delete {instance} --zone={zone} --delete-disks=all"
        )


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_cluster_create(
    name: Annotated[str, typer.Argument(help="cluster name", envvar="CLUSTER")],
    zone: Annotated[str, typer.Option(help="GC Zone", envvar="ZONE")] = "us-central1-b",
):
    """
    Create a kubernetes cluster in GC
    """
    run_shell_command(f"gcloud container clusters create {name} --zone={zone}")


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def gcloud_cluster_delete(
    name: Annotated[str, typer.Argument(help="cluster name", envvar="CLUSTER")],
    zone: Annotated[str, typer.Option(help="GC Zone", envvar="ZONE")] = "us-central1-b",
):
    """
    Delete a kubernetes cluster in GC
    """
    run_shell_command(f"gcloud container clusters delete {name} --zone={zone}")


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def cloud_install_cibutler(
    host: Annotated[str, typer.Argument(help="host", envvar="HOST")] = None,
    target: Annotated[str, typer.Option(help="target")] = "microk8s",
):
    """
    Run CI Butler install on remote linux host via ssh
    """
    remote_user = ssh(command="whoami", host=host)
    start_time = time.time()
    with console.status(f"Installing on {host}..."):
        with Connection(host) as c:
            console.print(f"Running CIButler on {host} as user {remote_user}")
            c.run(".local/bin/cibutler --version")
            c.run(f".local/bin/cibutler check --target {target}")
            c.run(".local/bin/cibutler install -k --force")
    elapsed_time = time.time() - start_time
    console.print(
        f":white_check_mark: Installation completed on {host} in {elapsed_time:.2f} seconds"
    )


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
            c.run("sudo microk8s status --wait-ready")
            c.run("sudo microk8s enable dns ingress storage")
        with Connection(host) as c:
            c.run("cd ~/.kube && microk8s config > config")
        # with Connection(host) as c:
        # /data
        # c.run("sudo microk8s kubectl get -o yaml -n kube-system deploy hostpath-provisioner | \
    # sed 's~/var/snap/microk8s/common/default-storage~/data/snap/microk8s/common/default-storage~g' | \
    # sudo microk8s kubectl apply -f -")

    # c.run("sudo ufw allow in on cni0 && sudo ufw allow out on cni0")
    # c.run("sudo ufw default allow routed")
    elapsed_time = time.time() - start_time
    console.print(
        f":white_check_mark: Installation completed on {host} in {elapsed_time:.2f} seconds"
    )


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def cloud_install_ubuntu_k3s(
    host: Annotated[str, typer.Argument(help="host", envvar="HOST")] = None,
    hide: Annotated[bool, typer.Option(help="Hide output")] = False,
):
    """
    Install on remote ubuntu linux host via SSH with K3s
    """
    remote_user = ssh(command="whoami", host=host, hide=hide)
    start_time = time.time()
    with console.status(f"Installing on {host}..."):
        with Connection(host) as c:
            console.print(f"Installing on {host} as user {remote_user}")
            c.run("sudo apt-get update")
            c.run("sudo apt install -y curl python3-pip pipx")
            c.run("curl -sfL https://get.k3s.io | sh - ")
            c.run("sudo snap install helm --classic")
            c.run("sudo k3s kubectl get node")
            c.run("pipx ensurepath")
            c.run("pipx install hostsman")
            c.run(
                "sudo .local/share/pipx/venvs/hostsman/bin/hostsman -i osdu.localhost:127.0.0.1 osdu.local:127.0.0.1 airflow.localhost:127.0.0.1 airflow.local:127.0.0.1 minio.localhost:127.0.0.1 minio.local:127.0.0.1 keycloak.localhost:127.0.0.1 keycloak.local:127.0.0.1"
            )
            c.run(
                'pipx install cibutler --index-url https://community.opengroup.org/api/v4/projects/1558/packages/pypi/simple --pip-args="--extra-index-url=https://community.opengroup.org/api/v4/projects/148/packages/pypi/simple"'
            )
            c.run(".local/bin/cibutler --version")
            c.run("mkdir -p ~/.kube")
            c.run("sudo k3s kubectl config view --raw > $HOME/.kube/config")
            c.run("chown 600 $HOME/.kube/config")
            c.run("kubectl get node")

    # c.run("sudo ufw allow in on cni0 && sudo ufw allow out on cni0")
    # c.run("sudo ufw default allow routed")
    elapsed_time = time.time() - start_time
    console.print(
        f":white_check_mark: Installation completed on {host} in {elapsed_time:.2f} seconds"
    )


@diag_cli.command(rich_help_panel="Cloud Diagnostic Commands")
def cloud_install_rocky_microk8s(
    host: Annotated[str, typer.Argument(help="host", envvar="HOST")] = None,
    hide: Annotated[bool, typer.Option(help="Hide output")] = False,
):
    """
    Install on remote Rocky linux host via SSH with MicroK8s
    """
    remote_user = ssh(command="whoami", host=host, hide=hide)
    start_time = time.time()
    with console.status(f"Installing on {host}..."):
        with Connection(host) as c:
            console.print(f"Installing on {host} as user {remote_user}")
            c.run("sudo dnf -y update")
            c.run("sudo dnf install epel-release -y")
            c.run("sudo dnf install snapd -y")
            c.run("sudo ln -s /var/lib/snapd/snap /snap")
            c.run(
                "echo 'export PATH=$PATH:/var/lib/snapd/snap/bin' | sudo tee -a /etc/profile.d/snap.sh"
            )
            c.run("source /etc/profile.d/snap.sh")
            c.run("sudo systemctl enable --now snapd.socket")
            c.run("systemctl status snapd.socket")
            c.run("sudo setenforce 0")
            c.run(
                "sudo sed -i 's/^SELINUX=.*/SELINUX=permissive/g' /etc/selinux/config"
            )
            c.run("sudo apt install -y curl python3-pip pipx")
            c.run("sudo snap install microk8s --classic")
            c.run("sudo snap install helm --classic")
            c.run("sudo dnf install python3.11")
            c.run("sudo dnf install python3.11-pip -y")
            c.run("python3.11 -m pip install pipx")
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
        with Connection(host) as c:
            c.run("cd ~/.kube && microk8s config > config")

    # c.run("sudo ufw allow in on cni0 && sudo ufw allow out on cni0")
    # c.run("sudo ufw default allow routed")
    elapsed_time = time.time() - start_time
    console.print(
        f":white_check_mark: Installation completed on {host} in {elapsed_time:.2f} seconds"
    )


if __name__ == "__main__":
    diag_cli()
