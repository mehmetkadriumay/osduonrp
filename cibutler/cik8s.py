import typer
import subprocess
import shlex
import json
from pick import pick
from rich.console import Console
from kubernetes import client, config
from typing_extensions import Annotated
from cibutler.shell import run_shell_command
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

# in future will need from kubernetes.client import configuration
# and from kubernetes.client.rest import ApiException

console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

diag_cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)


@diag_cli.command(rich_help_panel="Kubernetes Diagnostic Commands")
def list_pods(
    incluster: Annotated[
        bool,
        typer.Option("--incluster", help="Use incluster config"),
    ] = False,
):
    """
    List pods via api - IP, namespace and name
    """
    # Configs can be set in Configuration class directly or using helper utility
    try:
        if incluster:
            config.load_incluster_config()
        else:
            config.load_kube_config()
    except config.config_exception.ConfigException as err:
        console.print(f":x: Error loading kube config: {err}")
        raise typer.Exit(1)
    except Exception as err:
        console.print(f":x: Error loading kube config: {err}")
        raise typer.Exit(1)

    k8s_api = client.CoreV1Api()
    ret = k8s_api.list_pod_for_all_namespaces(watch=False)
    for i in ret.items:
        console.print(
            "%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name)
        )


def list_nodes():
    """
    List nodes via api
    """
    config.load_kube_config()
    k8s_api = client.CoreV1Api()
    response = k8s_api.list_node()
    # console.print(response)
    return response


def kube_status():
    return list_nodes().items[0].status


def kube_allocatable():
    return kube_status().allocatable


def kube_allocatable_cpu():
    return int(kube_status().allocatable["cpu"])


def kube_allocatable_memory():
    return kube_status().allocatable["memory"]


def kube_istio_ready():
    output = subprocess.Popen(
        [
            "kubectl",
            "-n",
            "istio-system",
            "get",
            "deploy",
            "-o",
            "jsonpath",
            "--template",
            "{..readyReplicas}",
        ],
        stdout=subprocess.PIPE,
    ).communicate()[0]
    return output.decode("ascii").strip()


def kubepod_name(type):
    output = subprocess.Popen(
        [
            "kubectl",
            "get",
            "pods",
            "-l",
            "type=" + type,
            "-o",
            "jsonpath",
            "--template",
            "{..metadata.name}",
        ],
        stdout=subprocess.PIPE,
    ).communicate()[0]
    return output.decode("ascii").strip()


def kubepod_nodename(nodename):
    output = subprocess.Popen(
        [
            "kubectl",
            "get",
            "pods",
            "-l",
            "node-name=" + str(nodename),
            "-o",
            "jsonpath",
            "--template",
            "{..metadata.name}",
        ],
        stdout=subprocess.PIPE,
    ).communicate()[0]
    return output.decode("ascii").strip()


def describe(what="pods", label=None, thing=None):
    if thing:
        output = subprocess.Popen(
            ["kubectl", "describe", what, thing], stdout=subprocess.PIPE
        ).communicate()[0]
    elif label:
        output = subprocess.Popen(
            ["kubectl", "describe", what, "-l", label], stdout=subprocess.PIPE
        ).communicate()[0]
    else:
        output = subprocess.Popen(
            ["kubectl", "describe", what], stdout=subprocess.PIPE
        ).communicate()[0]
    return output.decode("ascii").strip()


def get_namespace(namespace):
    if namespace:
        output = subprocess.Popen(
            ["kubectl", "describe", "namespaces", namespace], stdout=subprocess.PIPE
        ).communicate()[0]
    else:
        output = subprocess.Popen(
            ["kubectl", "get", "namespace", "--show-labels"], stdout=subprocess.PIPE
        ).communicate()[0]
    return output.decode("ascii").strip()


def get_services():
    """
    Get k8s services
    """
    output = subprocess.Popen(
        ["kubectl", "get", "services"], stdout=subprocess.PIPE
    ).communicate()[0]
    return output.decode("ascii").strip()


def get_clusters():
    """
    List the clusters kubectl knows about
    """
    output = subprocess.Popen(
        ["kubectl", "config", "get-clusters"], stdout=subprocess.PIPE
    ).communicate()[0]
    return output.decode("ascii").strip()


def cluster_info():
    """
    List the clusters kubectl knows about
    """
    output = subprocess.Popen(
        ["kubectl", "cluster-info"], stdout=subprocess.PIPE
    ).communicate()[0]
    return output.decode("ascii").strip()


def delete_item(name, grace_period: int = 1):
    console.print(f"Deleting {name}...")
    output = subprocess.Popen(
        ["kubectl", "delete", name, "--all", f"--grace-period={grace_period}"],
        stdout=subprocess.PIPE,
    ).communicate()[0]
    return output.decode("ascii").strip()


def delete_all(namespace: str = "default", grace_period: int = 1):
    output = subprocess.Popen(
        [
            "kubectl",
            "delete",
            "all",
            "--all",
            "-n",
            "namespace",
            f"--grace-period={grace_period}",
        ],
        stdout=subprocess.PIPE,
    ).communicate()[0]
    return output.decode("ascii").strip()


def kubectl_get(opt="vs"):
    try:
        output = subprocess.run(["kubectl", "get", opt], capture_output=True)  # nosec
    except subprocess.CalledProcessError as err:
        return str(err)
    else:
        return output.stdout.decode("ascii").strip()


def get_ingress_ip():
    output = subprocess.Popen(
        [
            "kubectl",
            "get",
            "--no-headers",
            "svc",
            "-n",
            "istio-system",
            "istio-ingress",
        ],
        stdout=subprocess.PIPE,
    ).communicate()[0]  # nosec
    return output.decode("ascii").strip().split()[2]


@diag_cli.command(rich_help_panel="Kubernetes Diagnostic Commands")
def pods_not_running():
    """
    Show pods that are not running
    """
    console.print(get_pods_not_running())


def get_pods_not_running():
    cmd = "kubectl get pods -o jsonpath='{range .items[?(@.status.containerStatuses[-1:].state.waiting)]}{.metadata.name}: {@.status.containerStatuses[*].state.waiting.reason}{\"\\n\"}{end}'"  # nosec
    args = shlex.split(cmd)
    output = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
    return output.decode("ascii").strip()


def get_deployment_status(deployment):
    cmd = f"kubectl get deploy {deployment} -o jsonpath='{{.status}}'"  # nosec
    args = shlex.split(cmd)
    output = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
    data = output.decode("ascii").strip()
    if data:
        return json.loads(data)


@cli.command(rich_help_panel="k8s Related Commands")
def use_context(
    context: Annotated[
        str, typer.Option("--context", "-c", help="Kubernetes Context")
    ] = None,
):
    """
    Sets the current kubernetes context.

    Useful when working with multiple kubernetes environments
    """
    if context:
        console.print(usecontext(context))
    else:
        console.print(usecontext(selectcontext()))


@cli.command(rich_help_panel="k8s Related Commands")
def current_context():
    """
    Display current kubernetes context
    """
    context = get_currentcontext()
    if context:
        console.print(context)


def get_currentcontext():
    # kubectl config view -o template --template='{{ index . "current-context" }}'
    output = subprocess.Popen(
        ["kubectl", "config", "current-context"], stdout=subprocess.PIPE
    ).communicate()[0]  # nosec
    return output.decode("ascii").strip()


def get_current_valid_context():
    context = get_currentcontext()
    if not context:
        error_console.print(
            "No current kubernetes context set. Try using 'use-context' command."
        )
        raise typer.Abort()
    else:
        return context


def usecontext(context: str = "docker-desktop"):
    output = subprocess.Popen(
        ["kubectl", "config", "use-context", context], stdout=subprocess.PIPE
    ).communicate()[0]  # nosec
    return output.decode("ascii").strip()


def selectcontext():
    try:
        contexts, active_context = config.list_kube_config_contexts()
    except config.ConfigException as err:
        error_console.print(err)
        console.print(
            "Try setting to a known good context 'use-context -c docker-desktop'"
        )
        raise typer.Abort()

    if not contexts:
        error_console.print("Cannot find any context in kube-config file.")
        return
    contexts = [context["name"] for context in contexts]
    active_index = contexts.index(active_context["name"])
    option, _ = pick(
        contexts, title="Pick the context to load", default_index=active_index
    )
    return option


@diag_cli.command(rich_help_panel="Kubernetes Diagnostic Commands")
def services():
    """
    Show virtual services
    """
    console.print(kubectl_get())


@diag_cli.command(rich_help_panel="Kubernetes Diagnostic Commands")
def ready():
    """
    Pods ready
    """
    pods = get_pods_not_running()
    if pods:
        console.print(":x: Pods Not Ready")
        console.print(pods)
        typer.Exit(1)
    else:
        console.print(":thumbs_up: Pods Ready")


@diag_cli.command(rich_help_panel="Kubernetes Diagnostic Commands")
def ingress():
    """
    Show ingress IP
    """
    console.print(get_ingress_ip())


def get_storage_classes():
    """
    Get storage classes
    """
    try:
        output = subprocess.run(
            ["kubectl", "get", "sc", "-o", "json"], capture_output=True, check=True
        )
        return json.loads(output.stdout.decode("utf-8"))
    except subprocess.CalledProcessError as err:
        error_console.print(f":x: Error getting storage classes: {err}")
        raise typer.Exit(1)


@diag_cli.command(rich_help_panel="Kubernetes Diagnostic Commands")
def add_sc(
    name: Annotated[
        str,
        typer.Option("--name", help="Name of the Storage Class"),
    ] = "standard",
    force: Annotated[
        bool, typer.Option("--force", help="Create Storage Class even if it exists")
    ] = False,
    ignore: Annotated[
        bool, typer.Option("--ignore", help="Don't raise error if Storage Class exists")
    ] = False,
):
    """
    Add Storage Class with docker.io/hostpath provisioner to Kubernetes cluster if it does not already exist.

    If it exists, it will not be overwritten unless --force is specified.
    The Storage Class will be created with the name specified by --name.

    """

    classes = get_storage_classes()
    logger.debug(f"Available Storage Classes: {classes}")
    for sc in classes.get("items", []):
        if sc.get("metadata", {}).get("name") == name:
            if force:
                console.log(
                    f":warning: Storage Class {name} already exists, but will be overwritten due to --force option"
                )
            elif ignore:
                console.log(
                    f":information_source: Storage Class {name} already exists, ignoring due to --ignore option"
                )
                return
            else:
                error_console.print(
                    f":x: Storage Class {name} already exists, use --force to overwrite"
                )
                raise typer.Exit(1)

    yaml = f"""apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: {name}
  annotations:
    storageclass.kubernetes.io/is-default-class: "false" # Optional, to make it the default
provisioner: docker.io/hostpath
reclaimPolicy: Delete # Or Retain, depending on your needs
volumeBindingMode: Immediate # Or WaitForFirstConsumer
    """.strip()

    filename = Path.home().joinpath("sc.yaml")
    with open(filename, "w") as f:
        f.write(yaml)

    console.log(f"Adding Storage Class {name}...")
    try:
        run_shell_command(f"kubectl apply -f {filename}")
        console.log(f":thumbs_up: Storage Class {name} Added")
        os.remove(filename)  # Clean up the temporary file
    except subprocess.CalledProcessError as err:
        error_console.print(f":x: Error adding Storage Class {name}: {err}")
        raise typer.Exit(1)


if __name__ == "__main__":
    cli()
