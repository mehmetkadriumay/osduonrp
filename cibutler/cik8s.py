import typer
import subprocess
import shlex
import json
from pick import pick
from rich.console import Console
from kubernetes import client, config

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
def list_pods():
    """
    List pods via api - IP, namespace and name
    """
    # Configs can be set in Configuration class directly or using helper utility
    config.load_kube_config()

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


def delete_item(name):
    console.print(f"Deleting {name}...")
    output = subprocess.Popen(
        ["kubectl", "delete", name, "--all"], stdout=subprocess.PIPE
    ).communicate()[0]
    return output.decode("ascii").strip()


def kubectl_get(opt="vs"):
    try:
        output = subprocess.run(["kubectl", "get", opt], capture_output=True)
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
    ).communicate()[0]
    return output.decode("ascii").strip().split()[2]


def get_pods_not_running():
    cmd = "kubectl get pods -o jsonpath='{range .items[?(@.status.containerStatuses[-1:].state.waiting)]}{.metadata.name}: {@.status.containerStatuses[*].state.waiting.reason}{\"\\n\"}{end}'"
    args = shlex.split(cmd)
    output = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
    return output.decode("ascii").strip()


def get_deployment_status(deployment):
    cmd = f"kubectl get deploy {deployment} -o jsonpath='{{.status}}'"
    args = shlex.split(cmd)
    output = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
    data = output.decode("ascii").strip()
    if data:
        return json.loads(data)


@cli.command(rich_help_panel="k8s Related Commands")
def use_context(context: str = None):
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
    console.print(currentcontext())


def currentcontext():
    # kubectl config view -o template --template='{{ index . "current-context" }}'
    output = subprocess.Popen(
        ["kubectl", "config", "current-context"], stdout=subprocess.PIPE
    ).communicate()[0]
    return output.decode("ascii").strip()


def usecontext(context):
    output = subprocess.Popen(
        ["kubectl", "config", "use-context", context], stdout=subprocess.PIPE
    ).communicate()[0]
    return output.decode("ascii").strip()


def selectcontext():
    contexts, active_context = config.list_kube_config_contexts()
    if not contexts:
        print("Cannot find any context in kube-config file.")
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


if __name__ == "__main__":
    cli()
