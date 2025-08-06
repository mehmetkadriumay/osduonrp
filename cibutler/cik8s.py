import typer
import subprocess
import shlex
import json
import platform
from pick import pick
from rich.console import Console
from rich.progress import track
from kubernetes import client, config
from kubernetes.client.rest import ApiException
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
    save: Annotated[bool, typer.Option(help="Save to file")] = False,
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
    if save:
        txt_name = "pods_list.txt"
        json_name = "pods_list.json"
        with open(txt_name, "w") as f:
            for i in ret.items:
                f.write(
                    f"{i.status.pod_ip}\t{i.metadata.namespace}\t{i.metadata.name}\t{i.status.phase}\n"
                )
        console.print(f":white_check_mark: Pods list saved to {txt_name}")
        logger.info(f"Pods list saved to {txt_name}")
        with open(json_name, "w") as f:
            f.write(str(ret))
        console.print(f":white_check_mark: Pods list saved to {json_name}")
        for i in track(ret.items, description="Saving pod logs and descriptions..."):
            # console.print(f"Saving logs and description for pod {i.metadata.name}...")
            describe_txt = get_describe(
                what="pod", thing=i.metadata.name, namespace=i.metadata.namespace
            )
            with open(f"{i.metadata.name}_describe.txt", "w") as descf:
                descf.write(describe_txt)
                # console.print(f":white_check_mark: saved describe for {i.metadata.name} to {i.metadata.name}_describe.txt")
            pod_log = pod_logs(pod_name=i.metadata.name, namespace=i.metadata.namespace)
            with open(f"{i.metadata.name}_logs.txt", "w") as logf:
                logf.write(pod_log)
                # console.print(f":white_check_mark: saved logs for {i.metadata.name} to {i.metadata.name}_logs.txt")

        return txt_name, json_name
    else:
        for i in ret.items:
            console.print(
                "%s\t%s\t%s\t%s"
                % (
                    i.status.pod_ip,
                    i.metadata.namespace,
                    i.metadata.name,
                    i.status.phase,
                )
            )


def list_nodes():
    """
    List nodes via api
    """
    config.load_kube_config()
    try:
        k8s_api = client.CoreV1Api()
        response = k8s_api.list_node()
    except ApiException as err:
        error_console.print(f":x: Error talking to kubernetes API: {err}")
        raise typer.Exit(1)
    except Exception as err:
        error_console.print(f":x: Error talking to kubernetes API: {err}")
        raise typer.Exit(1)
    logger.info(response)
    return response


def node_status(name: str):
    config.load_kube_config()
    k8s_api = client.CoreV1Api()
    response = k8s_api.read_node_status(name)
    logger.info(response)
    return response


def kube_status():
    return list_nodes().items[0].status


def kube_log_node_info():
    logger.info(kube_status().node_info)


def kube_allocatable():
    return kube_status().allocatable


def kube_allocatable_cpu():
    """
    Get the allocatable CPU
    """
    cpu = kube_status().allocatable["cpu"]
    logger.info(f"k8s cpu {cpu}")
    if "m" in cpu:
        return cpu
    else:
        return int(kube_status().allocatable["cpu"])


def kube_allocatable_memory():
    """Get the allocatable memory in bytes."""
    return kube_status().allocatable["memory"]


def kube_capacity_memory():
    """Get the capacity memory in bytes."""
    return kube_status().capacity["memory"]


def kube_allocatable_memory_gb():
    """Get the allocatable memory in GB."""
    k8s_memory = kube_allocatable_memory()
    if k8s_memory.endswith("Ki"):
        ki = int(k8s_memory.replace("Ki", ""))
        return ki / 1024 / 1024
    else:
        return None


def kube_capacity_memory_gb():
    """Get the capacity memory in GB."""
    k8s_memory = kube_capacity_memory()
    if k8s_memory.endswith("Ki"):
        ki = int(k8s_memory.replace("Ki", ""))
        return ki / 1024 / 1024
    else:
        return None


def kube_istio_ready():
    """Check if Istio is ready in the cluster."""
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
    retval = output.decode("ascii").strip()
    console.print(f"kube_istio_ready: {retval}")
    logger.info(f"kube_istio_ready: {retval}")
    return retval


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


@diag_cli.command(rich_help_panel="Kubernetes Diagnostic Commands")
def describe(
    save: Annotated[bool, typer.Option(help="Save to file")] = False,
    what: Annotated[str, typer.Option(help="What to describe")] = "pods",
    label: Annotated[str, typer.Option(help="Label selector")] = None,
    thing: Annotated[str, typer.Option(help="Specific resource to describe")] = None,
    namespace: Annotated[str, typer.Option(help="Kubernetes namespace")] = "default",
):
    """Describe a Kubernetes resource."""
    if save:
        name = f"{what}_describe.txt"
        with open(name, "w") as f:
            f.write(
                get_describe(what=what, label=label, thing=thing, namespace=namespace)
            )
        console.print(f":white_check_mark: Describe {what} saved to {name}")
        logger.info(f"Describe {what} saved to {name}")
        return name
    else:
        console.print(
            get_describe(what=what, label=label, thing=thing, namespace=namespace)
        )


def get_describe(what="pods", label=None, thing=None, namespace="default"):
    """Get the description of a Kubernetes resource."""
    try:
        if thing:
            output = subprocess.Popen(
                ["kubectl", "-n", namespace, "describe", what, thing],
                stdout=subprocess.PIPE,
            ).communicate()[0]
        elif label:
            output = subprocess.Popen(
                ["kubectl", "-n", namespace, "describe", what, "-l", label],
                stdout=subprocess.PIPE,
            ).communicate()[0]
        else:
            output = subprocess.Popen(
                ["kubectl", "-n", namespace, "describe", what], stdout=subprocess.PIPE
            ).communicate()[0]
        return output.decode("utf-8").strip()
    except Exception as err:
        error_console.print(f":x: Error describing {what} {thing}: {err}")


def pod_containers(pod_name, namespace="default"):
    try:
        output = subprocess.Popen(
            [
                "kubectl",
                "get",
                "pod",
                pod_name,
                "-n",
                namespace,
                "-o",
                "jsonpath={.spec.containers[*].name}",
            ],
            stdout=subprocess.PIPE,
        ).communicate()[0]
        return output.decode("utf-8").strip().split()
    except subprocess.CalledProcessError as err:
        error_console.print(f":x: Error getting containers for pod {pod_name}: {err}")
        return f"Error getting containers for pod {pod_name}: {err}"
    except Exception as err:
        error_console.print(f":x: Error getting containers for pod {pod_name}: {err}")
        return f"Error getting containers for pod {pod_name}: {err}"


def pod_logs(pod_name, namespace="default"):
    containers = pod_containers(pod_name=pod_name, namespace=namespace)
    for container in containers:
        logger.info(
            f"Getting logs for pod {pod_name} in namespace {namespace} for container: {container}"
        )
        try:
            output = subprocess.Popen(
                ["kubectl", "logs", pod_name, "-c", container, "-n", namespace],
                stdout=subprocess.PIPE,
            ).communicate()[0]
            return output.decode("utf-8").strip()
        except subprocess.CalledProcessError as err:
            error_console.print(f":x: Error getting logs for pod {pod_name}: {err}")
            return f"Error getting logs for pod {pod_name}: {err}"
        except Exception as err:
            error_console.print(f":x: Error getting logs for pod {pod_name}: {err}")
            return f"Error getting logs for pod {pod_name}: {err}"


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


def delete_item(name, namespace="default", grace_period: int = 1):
    output = subprocess.Popen(
        [
            "kubectl",
            "delete",
            name,
            "--all",
            "-n",
            namespace,
            f"--grace-period={grace_period}",
        ],
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
            namespace,
            f"--grace-period={grace_period}",
        ],
        stdout=subprocess.PIPE,
    ).communicate()[0]
    return output.decode("ascii").strip()


def kubectl_get(opt="vs", namespace: str = "default"):
    try:
        output = subprocess.run(
            ["kubectl", "get", opt, "-n", namespace], capture_output=True
        )  # nosec
    except subprocess.CalledProcessError as err:
        return str(err)
    else:
        return output.stdout.decode("ascii").strip()


def get_ingress_ip(namespace: str = "istio-system"):
    output = subprocess.Popen(
        [
            "kubectl",
            "get",
            "--no-headers",
            "svc",
            "-n",
            namespace,
            "istio-ingress",
        ],
        stdout=subprocess.PIPE,
    ).communicate()[0]  # nosec
    return output.decode("ascii").strip().split()[2]


@diag_cli.command(rich_help_panel="Kubernetes Diagnostic Commands")
def pods_not_running(
    namespace: Annotated[
        str,
        typer.Option(
            "--namespace", "-n", help="Namespace to check for pods not running"
        ),
    ] = "default",
    save: Annotated[bool, typer.Option(help="Save to file")] = False,
):
    """
    Show pods that are not running
    """
    name = "pods_not_running.txt"
    if save:
        with open(name, "w") as f:
            f.write(get_pods_not_running(namespace=namespace))
        console.print(f":white_check_mark: Pods not running saved to {name}")
        logger.info(f"Pods not running saved to {name}")
        return name
    else:
        console.print(get_pods_not_running(namespace=namespace))


def get_pods_not_running(namespace: str = "default"):
    """
    Get pods that are not running in the specified namespace.
    """
    jsonpath = "'{range .items[?(@.status.containerStatuses[-1:].state.waiting)]}{.metadata.name}: {@.status.containerStatuses[*].state.waiting.reason}{\"\\n\"}{end}'"  # nosec
    cmd = f"kubectl get pods -n {namespace} -o jsonpath={jsonpath}"  # nosec
    args = shlex.split(cmd)
    output = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
    return output.decode("ascii").strip()


def get_deployment_status(deployment: str, namespace: str = "default"):
    cmd = f"kubectl get deploy {deployment} -n {namespace} -o jsonpath='{{.status}}'"  # nosec
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


def log_contexts():
    try:
        contexts, active_context = config.list_kube_config_contexts()
    except config.ConfigException as err:
        logger.info(f"no good context {err}")

    if not contexts:
        logger.info("Cannot find any context in kube-config file.")
    else:
        logger.info(f"contexts: {contexts}")


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
def services(
    namespace: Annotated[
        str, typer.Option("--namespace", "-n", help="Namespace to list services from")
    ] = "default",
    save: Annotated[bool, typer.Option(help="Save to file")] = False,
):
    """
    Show virtual services
    """
    if save:
        name = "services.txt"
        with open(name, "w") as f:
            f.write(kubectl_get("vs", namespace=namespace))
        console.print(f":white_check_mark: Services saved to {name}")
        logger.info(f"Services saved to {name}")
        return name
    else:
        console.print(kubectl_get(namespace=namespace))


@diag_cli.command(rich_help_panel="Kubernetes Diagnostic Commands")
def ready(
    namespace: Annotated[
        str, typer.Option("--namespace", "-n", help="Namespace to check for pods ready")
    ] = "default",
):
    """
    Pods ready
    """
    pods = get_pods_not_running(namespace=namespace)
    if pods:
        console.print(f":x: Pods Not Ready in {namespace}")
        console.print(pods)
        typer.Exit(1)
    else:
        console.print(f":thumbs_up: Pods Ready in {namespace}")


@diag_cli.command(rich_help_panel="Kubernetes Diagnostic Commands")
def ingress():
    """
    Show ingress IP
    """
    console.print(get_ingress_ip())


def get_pvcs(namespace: str = "default"):
    """
    Get persistent volume claims
    """
    try:
        output = subprocess.run(
            ["kubectl", "get", "pvc", "-n", namespace, "-o", "json"],
            capture_output=True,
            check=True,
        )
        return json.loads(output.stdout.decode("utf-8"))
    except subprocess.CalledProcessError as err:
        error_console.print(f":x: Error getting PVCs: {err}")
        raise typer.Exit(1)


@diag_cli.command(rich_help_panel="Kubernetes Diagnostic Commands")
def list_pvcs(
    namespace: Annotated[
        str, typer.Option("--namespace", "-n", help="Namespace to list PVCs from")
    ] = "default",
):
    """
    List persistent volume claims in the specified namespace.
    """
    output = get_pvcs(namespace)
    if not output.get("items"):
        console.print(f":information_source: No PVCs found in namespace '{namespace}'")
    console.print(":page_facing_up: Persistent Volume Claims in namespace:", namespace)
    for pvc in output.get("items", []):
        name = pvc.get("metadata", {}).get("name", "Unknown")
        status = pvc.get("status", {}).get("phase", "Unknown")
        size = (
            pvc.get("spec", {})
            .get("resources", {})
            .get("requests", {})
            .get("storage", "Unknown")
        )
        console.print(f"{name} - Status: {status}, Size: {size}")


def get_storage_classes(save: bool = False):
    """
    Get storage classes
    """
    try:
        output = subprocess.run(
            ["kubectl", "get", "sc", "-o", "json"], capture_output=True, check=True
        )
        if save:
            name = "storage_classes.json"
            with open(name, "w") as f:
                f.write(output.stdout.decode("utf-8"))
            console.print(f":white_check_mark: Storage classes saved to {name}")
            logger.info(f"Storage classes saved to {name}")
            return name
        return json.loads(output.stdout.decode("utf-8"))
    except subprocess.CalledProcessError as err:
        error_console.print(f":x: Error getting storage classes: {err}")
        raise typer.Exit(1)


@diag_cli.command(rich_help_panel="Kubernetes Diagnostic Commands")
def patch_all_pvcs(
    namespace: Annotated[
        str, typer.Option("--namespace", "-n", help="Namespace to patch PVCs in")
    ] = "default",
    patch_data: Annotated[
        str,
        typer.Option(
            "--data",
            "-d",
            help="data string to patch PVCs with",
            rich_help_panel="JSON string",
        ),
    ] = '{"metadata": {"finalizers": null}}',  # Default patch to remove finalizers
):
    """
    Patch all Persistent Volume Claims (PVCs) in the specified namespace with the provided data.
    """
    output = get_pvcs(namespace)  # Ensure we can get PVCs in the namespace
    for pvc in output.get("items", []):
        name = pvc.get("metadata", {}).get("name", "Unknown")
        patch_pvc(pvc_name=name, namespace=namespace, patch_data=patch_data)


@diag_cli.command(rich_help_panel="Kubernetes Diagnostic Commands")
def patch_pvc(
    pvc_name: str,
    namespace: Annotated[
        str, typer.Option("--namespace", "-n", help="Namespace to patch PVC in")
    ] = "default",
    patch_data: Annotated[
        str,
        typer.Option(
            "--data",
            "-d",
            help="data string to patch PVC with",
            rich_help_panel="JSON string",
        ),
    ] = '{"metadata": {"finalizers": null}}',  # Default patch to remove finalizers  ,
):
    """
    Patch a Persistent Volume Claim (PVC) with the provided data.
    """
    if not patch_data:
        error_console.print(":x: No patch data provided.")
        raise typer.Exit(1)

    try:
        console.print(
            f"Patching PVC '{pvc_name}' in namespace '{namespace}' with data:"
        )
        console.print(f":wrench: Patching PVC '{pvc_name}'...")
        console.print(f":page_facing_up: Patch Data: {patch_data}")
        # Ensure the patch is a valid JSON string
        output = subprocess.run(
            ["kubectl", "patch", "pvc", pvc_name, "-n", namespace, "-p", patch_data],
            capture_output=True,
            check=True,
        )
        console.print(f":thumbs_up: PVC '{pvc_name}' patched successfully.")
        return output.stdout.decode("utf-8")
    except subprocess.CalledProcessError as err:
        error_console.print(f":x: Error patching PVC '{pvc_name}': {err}")
        logging.error(f"Error patching PVC '{pvc_name}': {err}")


@diag_cli.command(rich_help_panel="Kubernetes Diagnostic Commands")
def add_sc(
    name: Annotated[
        str,
        typer.Option("--name", help="Name of the Storage Class"),
    ] = "standard",
    provisioner: Annotated[
        str,
        typer.Option("--provisioner", "-p", help="Provisioner"),
    ] = "docker.io/hostpath",
    force: Annotated[
        bool, typer.Option("--force", help="Create Storage Class even if it exists")
    ] = False,
    ignore: Annotated[
        bool, typer.Option("--ignore", help="Don't raise error if Storage Class exists")
    ] = False,
    preview: Annotated[bool, typer.Option("--preview", help="Preview")] = False,
):
    """
    Add Storage Class to Kubernetes cluster if it does not already exist.

    If it exists, it will not be overwritten unless --force is specified.
    The Storage Class will be created with the name specified by --name.

    Provisioner examples:
    * MicroK8s microk8s.io/hostpath
    * Docker docker.io/hostpath
    * K3d rancher.io/local-path
    * K3S rancher.io/local-path

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
                logger.info(
                    f"Storage Class {name} already exists, ignoring due to --ignore option"
                )
                return True
            else:
                error_console.print(
                    f":x: Storage Class {name} already exists, use --force to overwrite"
                )
                raise typer.Exit(1)

    if preview:
        logger.info(f"Storage class {name} required")
        return False

    yaml = f"""apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: {name}
  annotations:
    storageclass.kubernetes.io/is-default-class: "false" # Optional, to make it the default
provisioner: {provisioner}
reclaimPolicy: Delete # Or Retain, depending on your needs
volumeBindingMode: Immediate # Or WaitForFirstConsumer
    """.strip()

    filename = Path.home().joinpath("sc.yaml")
    console.log(f"Writing to {filename}")
    with open(filename, "w") as f:
        f.write(yaml)

    console.log(f"Adding Storage Class {name}...")
    try:
        run_shell_command(f"kubectl apply -f '{filename}'")
        console.log(f":thumbs_up: Storage Class {name} Added")
        os.remove(filename)  # Clean up the temporary file
    except subprocess.CalledProcessError as err:
        error_console.print(f":x: Error adding Storage Class {name}: {err}")
        raise typer.Exit(1)


def log_kube_stats():
    """
    log kube stats
    """
    allocatable_gb_memory = kube_allocatable_memory_gb()
    capacity_gb_memory = kube_capacity_memory_gb()
    allocatable_cpu = kube_allocatable_cpu()
    logger.info(
        f"After istio Kubernetes RAM: {allocatable_gb_memory:.2f}/{capacity_gb_memory:.2f} GiB CPU: {allocatable_cpu}"
    )


@diag_cli.command(rich_help_panel="Kubernetes Diagnostic Commands")
def get_cluster_ip(
    name: Annotated[
        str,
        typer.Option("--name", help="Name of the Service"),
    ] = "istio-ingress",
    namespace: Annotated[
        str,
        typer.Option("--namespace", help="Namespace"),
    ] = "istio-system",
    host: Annotated[
        bool, typer.Option("--host", help="Show with gateway names")
    ] = False,
):
    """
    Get cluster-ip of a service
    """
    try:
        config.load_kube_config()
        k8s_api = client.CoreV1Api()
        service = k8s_api.read_namespaced_service(name=name, namespace=namespace)
        if host:
            ip = service.spec.cluster_ip
            console.print(
                f"osdu.localhost:{ip} osdu.local:{ip} airflow.localhost:{ip} airflow.local:{ip} minio.localhost:{ip} minio.local:{ip} keycloak.localhost:{ip} keycloak.local:{ip}"
            )
        else:
            console.print(service.spec.cluster_ip)

    except config.config_exception.ConfigException as err:
        console.print(f":x: Error loading kube config: {err}")
        raise typer.Exit(1)
    except ApiException as err:
        console.print(f":x: API Exception name: {name} namespace: {namespace}: {err}")
        raise typer.Exit(1)
    except Exception as err:
        console.print(f":x: Error loading kube config: {err}")
        raise typer.Exit(1)


if __name__ == "__main__":
    cli()
