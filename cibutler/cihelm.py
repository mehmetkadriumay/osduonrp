import subprocess
from rich.console import Console
import typer
import asyncio
from pyhelm3 import Client, Chart, ChartNotFoundError, CommandCancelledError
from pydantic import ValidationError
import typing
from cibutler.shell import run_shell_command
from cibutler.releases import select_version
from pathlib import Path
import re
import shutil
import logging

from typing_extensions import Annotated
from pydantic import (
    Field,
    DirectoryPath,
    FilePath,
    HttpUrl,
)

logger = logging.getLogger(__name__)

console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

diag_cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

Name = Annotated[str, Field(pattern=r"^[a-z0-9-]+$")]
OCIPath = Annotated[str, Field(pattern=r"oci:\/\/*")]


class OCIChart(Chart):
    ref: typing.Union[DirectoryPath, FilePath, HttpUrl, OCIPath, Name] = Field(
        ...,
    )


async def get_chart_oci(self, chart_ref, *, devel=False, repo=None, version=None):
    metadata = await self._command.show_chart(
        chart_ref, devel=devel, repo=repo, version=version
    )
    return OCIChart(_command=self._command, ref=chart_ref, repo=repo, metadata=metadata)


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
    logger.info(f"Uninstalling helm {name} in namespace {namespace}")
    output = subprocess.Popen(
        ["helm", "uninstall", name, "-n", namespace], stdout=subprocess.PIPE
    ).communicate()[0]
    return output.decode("ascii").strip()


@diag_cli.command(rich_help_panel="Helm Diagnostic Commands")
def helm_details():
    """
    Helm list via python
    """
    asyncio.run(helm_list_details_async())


async def helm_list_details_async():
    client = Client()

    # List the deployed releases
    releases = await client.list_releases(all=True, all_namespaces=True)
    for release in releases:
        revision = await release.current_revision()
        chart_metadata = await revision.chart_metadata()
        console.print(
            release.name,
            release.namespace,
            revision.revision,
            str(revision.status),
            chart_metadata.name,
            chart_metadata.version,
        )


@diag_cli.command(rich_help_panel="Helm Diagnostic Commands")
def helm_remove_repo(repo: str = "istio"):
    """
    Remove istio helm repo
    """
    console.print(f":pushpin: Removing helm repo {repo}")
    run_shell_command(f"helm repo remove {repo}")
    console.print(f":surfer: Done! {repo} helm repo removed")
    return True


@diag_cli.command(rich_help_panel="Helm Diagnostic Commands")
def show_chart(
    chart_ref: Annotated[
        str, typer.Argument(help="Ref or URL of Chart")
    ] = "oci://community.opengroup.org:5555/osdu/platform/security-and-compliance/policy/cimpl-helm/cimpl-policy-deploy",
    repo: Annotated[str, typer.Option(help="Repo. (Not for OCI usage)")] = None,
    version: Annotated[
        str, typer.Option("--version", "-v", help="Version")
    ] = "0.0.7-cimpld9e282b9",
):
    """
    Helm show chart details
    """
    asyncio.run(helm_get_chart_async(chart_ref=chart_ref, repo=repo, version=version))


async def helm_get_chart_async(
    chart_ref: str,
    repo: str,
    version: str,
    devel=False,
):
    # client = Client()
    # Monkey patch the get_chart method of the Client class
    Client.get_chart = get_chart_oci
    client = Client()

    with console.status(f"Getting details on chart {chart_ref}..."):
        # Fetch a chart
        try:
            logger.info(
                f"Fetching chart {chart_ref} from repo {repo} with version {version}, devel={devel}"
            )
            chart = await client.get_chart(
                chart_ref=chart_ref, repo=repo, version=version, devel=devel
            )
        except ChartNotFoundError as err:
            error_console.print(err)
            raise typer.Exit(1)
        except ValidationError as err:
            error_console.print(err)
            raise typer.Exit(1)
        except CommandCancelledError as err:
            error_console.print(err)
            raise typer.Abort()

    console.print(
        chart.metadata.name,
        chart.metadata.version,
        chart.metadata.app_version,
        chart.ref,
    )
    with console.status(f"Getting readme on chart {chart_ref}..."):
        try:
            console.print(await chart.readme())
        except TypeError:
            # no readme in chart
            # raise typer.Exit(0)
            pass
        except CommandCancelledError as err:
            error_console.print(err)
            raise typer.Abort()
    return chart


@diag_cli.command(rich_help_panel="Helm Diagnostic Commands")
def helm_install_or_upgrade(
    release_name: str = "cimpl-policy-deploy",
    chart_ref: Annotated[
        str, typer.Argument(help="Ref or URL of Chart")
    ] = "oci://community.opengroup.org:5555/osdu/platform/security-and-compliance/policy/cimpl-helm/cimpl-policy-deploy",
    repo: Annotated[str, typer.Option(help="Repo. (Not for OCI usage)")] = None,
    version: Annotated[
        str, typer.Option("--version", "-v", help="Version")
    ] = "0.0.7-cimpld9e282b9",
    atomic: Annotated[bool, typer.Option(help="Atomic")] = False,
    wait: Annotated[bool, typer.Option(help="Wait")] = False,
    dry_run: Annotated[bool, typer.Option(help="Dry Run")] = False,
):
    """
    Helm install or upgrade
    """
    asyncio.run(
        helm_install_or_upgrade_async(
            chart_ref=chart_ref,
            release_name=release_name,
            repo=repo,
            version=version,
            atomic=atomic,
            wait=wait,
            dry_run=dry_run,
        )
    )


async def helm_install_or_upgrade_async(
    chart_ref: str,
    release_name: str,
    repo: str,
    version: str,
    atomic: bool = False,
    wait: bool = False,
    dry_run: bool = True,
):
    # Install or upgrade a release

    values = {"installCRDs": True}
    client = Client()
    # Monkey patch the get_chart method of the Client class
    Client.get_chart = get_chart_oci

    chart = await helm_get_chart_async(chart_ref=chart_ref, repo=repo, version=version)
    logger.info(
        f"Installing or upgrading helm {chart_ref} with release name {release_name}, version {version}, atomic={atomic}, wait={wait}, dry_run={dry_run}"
    )
    with console.status(f"Installing/upgrading {chart_ref}..."):
        try:
            revision = await client.install_or_upgrade_release(
                release_name,
                chart,
                values,
                atomic=atomic,
                wait=wait,
                dry_run=dry_run,
            )
        except CommandCancelledError as err:
            error_console.print(err)
            raise typer.Abort()

    console.print(
        revision.release.name,
        revision.release.namespace,
        revision.revision,
        str(revision.status),
        revision.description,
    )

    if dry_run:
        console.print(revision)


def helm_list():
    """
    Return list from helm
    """
    try:
        output = subprocess.run(["helm", "list", "-a", "-A"], capture_output=True)  # nosec
    except subprocess.CalledProcessError as err:
        return str(err)
    else:
        return output.stdout.decode("ascii").strip()


@diag_cli.command(rich_help_panel="Helm Diagnostic Commands")
def helm_pull(
    dir: Annotated[str, typer.Option(help="Directory to save the chart")] = None,
    force: Annotated[
        bool, typer.Option("--force", help="Delete existing directory if it exists")
    ] = False,
):
    """
    Pull the helm chart to a directory for local inspection and testing.
    """
    version, source = select_version()
    if dir is None:
        dir = str(Path.home() / f"osdu-cimpl-{version}")

    if Path(dir).exists():
        if force:
            with console.status(f"Removing existing directory {dir}..."):
                shutil.rmtree(dir)
                console.print(f"Removed existing directory: {dir}")
        else:
            error_console.print(f"Directory {dir} already exists. Please remove it or use --force.")
            raise typer.Abort()

    run_shell_command(
        f"helm pull {source} --version {version} --untar --untardir {dir}"
        )
    console.print(f"Helm chart pulled to {dir}")

def helm_template_cmd(version, source, set=None):
    try:
        if set:
            output = subprocess.Popen(
                ["helm", "template", source, "--version", version, "--set", set],
                stdout=subprocess.PIPE,
            ).communicate()[0]
        else:
            # Default command without additional set values
            # This will use the default values from the chart
            # and will not include any additional set values
            output = subprocess.Popen(
                ["helm", "template", source, "--version", version],
                stdout=subprocess.PIPE,
            ).communicate()[0]
        return output.decode("utf-8").strip()
    except subprocess.CalledProcessError as err:
            error_console.print(f":x: Error getting template for {source}: {err}")
    except Exception as err:
            error_console.print(f":x: Error getting template for {source}: {err}")

@diag_cli.command(rich_help_panel="Helm Diagnostic Commands")
def helm_template(
    pull: Annotated[
        bool, typer.Option("--pull", "--download", help="Docker pull images from the chart")
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", help="Enable invalid yaml")
    ] = False,
    image: Annotated[
        bool, typer.Option("--image", help="Find images in the chart")
    ] = False,
    set: Annotated[
        str, typer.Option("--set", help="set values on the command line (can specify multiple or separate values with commas: key1=val1,key2=val2)")
    ] = None,
):
    """
    Helm template command to render the chart locally, get the images, or pull them for local testing.
    """
    version, source = select_version()
    if debug:
        run_shell_command(
            f"helm template {source} --version {version} --debug"
        )
    elif image or pull:
        response = helm_template_cmd(version, source, set)
        items = re.findall(r"image:\s*['\"]?([^'\"]+)['\"]?", response)
        for x in items:
            image_path = x.split()[0]  # Get the first part of the image string
            if pull:
                console.print(f"Pulling Docker image {image_path}...")
                run_shell_command(f"docker pull {image_path}")
            else:
                console.print(f"{image_path}")
    elif set:
        run_shell_command(
            f"helm template {source} --version {version} --set '{set}'"
        )
    else:
        run_shell_command(
            f"helm template {source} --version {version}"
        )


@diag_cli.command(rich_help_panel="Helm Diagnostic Commands", name="helm-list")
def helm_list_command(
    save: Annotated[bool, typer.Option(help="Save to file")] = False,
):
    """
    Show all releases in all namespaces
    """
    if save:
        name = "helm_list.txt"
        with open(name, "w") as f:
            f.write(helm_list())
        console.print(f":white_check_mark: Helm list saved to {name}")
        logger.info(f"Helm list saved to {name}")
        return name
    else:
        console.print(helm_list())


def helm_query(name):
    return name in helm_list()


if __name__ == "__main__":
    cli()
