import subprocess

from rich.console import Console
import typer

console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

diag_cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

# $ helm upgrade $CIMPL_SERVICE-deploy
#  oci://$CI_REGISTRY_IMAGE/cimpl-helm/$CIMPL_HELM_PACKAGE_NAME
# --version $CIMPL_HELM_PACKAGE_VERSION-$CIMPL_HELM_TAG --install --create-namespace --namespace=$CIMPL_HELM_NAMESPACE
# --wait --history-max=3
# --set global.onPremEnabled=true
# --set global.domain=$CIMPL_DOMAIN
# --set global.dataPartitionId=$CIMPL_TENANT
# --set data.serviceAccountName=$CIMPL_SERVICE
# --set data.bootstrapServiceAccountName=$CIMPL_BOOTSTRAP_SA
# --set data.cronJobServiceAccountName=$CIMPL_BOOTSTRAP_SA
# --set data.logLevel=INFO
# --set data.bucketPrefix="refi"
# --set data.groupId=$GROUP_ID
# --set data.sharedTenantName=$CIMPL_TENANT
# --set data.googleCloudProject=$CIMPL_PROJECT
# --set data.bucketName=$CIMPL_POLICY_BUCKET
# --set data.subscriberPrivateKeyId=$CIMPL_SUBSCRIBER_PRIVATE_KEY_ID
# --set rosa=true $CIMPL_HELM_SETS $CIMPL_HELM_TIMEOUT


def helm_install(
    name="osdu-baremetal",
    file="custom-values.yaml",
    chart="oci://community.opengroup.org:5555/osdu/platform/deployment-and-operations/infra-gcp-provisioning/gc-helm/osdu-gc-baremetal",
):
    # helm install -f custom-values.yaml osdu-baremetal oci://community.opengroup.org:5555/osdu/platform/deployment-and-operations/infra-gcp-provisioning/gc-helm/osdu-gc-baremetal
    output = subprocess.Popen(
        ["helm", "install", "-f", file, name, chart], stdout=subprocess.PIPE
    ).communicate()[0]
    return output.decode("ascii").strip()


def helm_uninstall(name="osdu-cimpl", namespace="default"):
    console.print(f"Uninstalling {name}...")
    output = subprocess.Popen(
        ["helm", "uninstall", name, "-n", namespace], stdout=subprocess.PIPE
    ).communicate()[0]
    return output.decode("ascii").strip()


def helm_list():
    """
    Return list from helm
    """
    try:
        output = subprocess.run(["helm", "list", "-a", "-A"], capture_output=True)
    except subprocess.CalledProcessError as err:
        return str(err)
    else:
        return output.stdout.decode("ascii").strip()


@diag_cli.command(rich_help_panel="Helm Diagnostic Commands", name="helm-list")
def helm_list_command():
    """
    Show all releases in all namespaces
    """
    console.print(helm_list())


def helm_query(name):
    return name in helm_list()


if __name__ == "__main__":
    cli()
