from rich.console import Console
import typer
import os
import requests
from osdu_api.auth.refresh_token import BaseTokenRefresher
from osdu_api.clients.entitlements.entitlements_client import EntitlementsClient
from osdu_api.clients.search.search_client import SearchClient
from osdu_api.clients.ingestion_workflow.ingestion_workflow_client import (
    IngestionWorkflowClient,
)
from osdu_api.clients.dataset.dataset_dms_client import DatasetDmsClient
from osdu_api.clients.storage.record_client import RecordClient
from osdu_api.clients.legal.legal_client import LegalClient
from osdu_api.model.entitlements.group_member import GroupMember
from osdu_api.model.search.query_request import QueryRequest
from requests.exceptions import ConnectionError
import tenacity
from typing_extensions import Annotated
import cibutler.cimpl as cimpl
import cibutler.conf as conf

"""
This limit OSDU functionality is to help verify OSDU is install and working correctly.
It also provides a convenient way to add users.
"""
console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

BASE_URL = "http://osdu.localhost"
CLOUD_PROVIDER = "baremetal"


def setup(base_url: str, realm: str = "osdu", client_id: str = "osdu-admin"):
    """
    Get a refresh token
    """
    client_secret = cimpl.get_keycloak_client_secret()
    os.environ[
        "KEYCLOAK_AUTH_URL"
    ] = f"http://keycloak.localhost/realms/{realm}/protocol/openid-connect/token"
    os.environ["KEYCLOAK_CLIENT_ID"] = client_id
    os.environ["KEYCLOAK_CLIENT_SECRET"] = client_secret
    os.environ["CLOUD_PROVIDER"] = CLOUD_PROVIDER
    os.environ["BASE_URL"] = base_url

    try:
        cimpl_token_refresher = BaseTokenRefresher()
        # token = cimpl_token_refresher.refresh_token()
        # if not token:
        # error_console.print("Error getting token")
    except tenacity.RetryError:
        error_console.print("RetryError when attempting to get refresh token")
        console.print("Is minikube tunnel up?")
        raise typer.Exit(1)
    return cimpl_token_refresher


@cli.command(rich_help_panel="Troubleshooting Commands")
def refresh_token(
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = BASE_URL,
    realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm")
    ] = "osdu",
    client_id: Annotated[str, typer.Option(help="ClientID")] = "osdu-admin",
):
    """
    Get OSDU refresh token from OSDU Python SDK
    """
    base_url = base_url.rstrip("/")
    cimpl_token_refresher = setup(base_url=base_url, realm=realm, client_id=client_id)
    token = cimpl_token_refresher.refresh_token()

    if token:
        console.print(token)
    else:
        error_console.print("Error getting token")


@cli.command(rich_help_panel="OSDU Related Commands")
def legal_tags(
    legal_tag: Annotated[str, typer.Option(help="Legal Tag")] = None,
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = BASE_URL,
    realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm")
    ] = "osdu",
    client_id: Annotated[str, typer.Option(help="ClientID")] = "osdu-admin",
):
    """
    Show legal tags

    --legal-tag allows lookup of a single legal tag
    """
    base_url = base_url.rstrip("/")
    cimpl_token_refresher = setup(base_url=base_url, realm=realm, client_id=client_id)
    legal_url = base_url + "/api/legal/v1"
    legal_client = LegalClient(
        legal_url=legal_url,
        provider=CLOUD_PROVIDER,
        data_partition_id="osdu",
        token_refresher=cimpl_token_refresher,
    )
    try:
        if legal_tag:
            r = legal_client.get_legal_tag(legal_tag_name=legal_tag)
        else:
            r = legal_client.list_legal_tags()
    except ConnectionError as err:
        error_console.print(f"ConnectionError {legal_url}: {err}")
        raise typer.Exit(1)
    if r.ok:
        console.print(r.json())
    else:
        error_console.print(f"Error {legal_url} list_legal_tags: {r.status_code}")


@cli.command(rich_help_panel="OSDU Related Commands")
def groups(
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = BASE_URL,
    realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm")
    ] = "osdu",
    client_id: Annotated[str, typer.Option(help="ClientID")] = "osdu-admin",
):
    """
    Groups for current user
    """
    with console.status("Connecting..."):
        base_url = base_url.rstrip("/")
        cimpl_token_refresher = setup(
            base_url=base_url, realm=realm, client_id=client_id
        )
        entitlements_url = base_url + "/api/entitlements/v2"
        entitlement_client = EntitlementsClient(
            entitlements_url=entitlements_url,
            provider=CLOUD_PROVIDER,
            data_partition_id="osdu",
            token_refresher=cimpl_token_refresher,
        )

    r = entitlement_client.get_groups_for_user()
    if r.ok:
        console.print(r.json())
    else:
        error_console.print(
            f"Error {entitlements_url} get_groups_for_user: {r.status_code}"
        )


@cli.command(rich_help_panel="OSDU Related Commands")
def group_members(
    group_email: Annotated[
        str, typer.Option("--group-email", "-g", help="Group email to lookup")
    ] = "users@osdu.group",
    role: Annotated[str, typer.Option("--role", "-r", help="Role")] = "MEMBER",
    limit: Annotated[int, typer.Option("--limit", "-l", help="Limit")] = 10,
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = BASE_URL,
    realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm")
    ] = "osdu",
    client_id: Annotated[str, typer.Option(help="ClientID")] = "osdu-admin",
):
    """
    Get all group members for a given group email
    """
    with console.status("Connecting..."):
        base_url = base_url.rstrip("/")
        cimpl_token_refresher = setup(
            base_url=base_url, realm=realm, client_id=client_id
        )
        entitlement_client = EntitlementsClient(
            entitlements_url=base_url + "/api/entitlements/v2",
            provider=CLOUD_PROVIDER,
            data_partition_id="osdu",
            token_refresher=cimpl_token_refresher,
        )

    r = entitlement_client.get_group_members(
        group_email=group_email, limit=limit, role=role
    )
    if r.ok:
        console.print(r.json())
    else:
        error_console.print(f"Error {r.status_code}")


@cli.command(rich_help_panel="OSDU Related Commands")
def group_add(
    email: str,
    group_email: str = "users@osdu.group",
    role: str = "MEMBER",
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = BASE_URL,
    realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm")
    ] = "osdu",
    client_id: Annotated[str, typer.Option(help="ClientID")] = "osdu-admin",
):
    """
    Add member email to group
    """
    base_url = base_url.rstrip("/")
    cimpl_token_refresher = setup(base_url=base_url, realm=realm, client_id=client_id)
    entitlement_client = EntitlementsClient(
        entitlements_url=base_url + "/api/entitlements/v2",
        provider=CLOUD_PROVIDER,
        data_partition_id="osdu",
        token_refresher=cimpl_token_refresher,
    )
    r = entitlement_client.create_group_member(
        group_email=group_email,
        group_member=GroupMember(email=email, role=role),
    )
    if r.ok:
        console.print(r.json())
    else:
        error_console.print(f"Error {r.status_code}")


@cli.command(rich_help_panel="OSDU Related Commands")
def search(
    kind: str = "*:*:*:*",
    query: str = "",
    limit: int = 10,
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = BASE_URL,
    realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm")
    ] = "osdu",
    client_id: Annotated[str, typer.Option(help="ClientID")] = "osdu-admin",
):
    """
    Simple OSDU Search
    """
    base_url = base_url.rstrip("/")
    cimpl_token_refresher = setup(base_url=base_url, realm=realm, client_id=client_id)
    search_client = SearchClient(
        search_url=base_url + "/api/search/v2",
        provider=CLOUD_PROVIDER,
        data_partition_id="osdu",
        token_refresher=cimpl_token_refresher,
    )
    r = search_client.query_records(QueryRequest(kind=kind, query=query, limit=limit))
    if r.ok:
        console.print(r.json())
    else:
        error_console.print(f"Search error {r.status_code}")


@cli.command(rich_help_panel="OSDU Related Commands")
def record(
    record_id: Annotated[str, typer.Argument(help="Storage Record")],
    get_retrieval_instructions: Annotated[
        bool, typer.Option(help="Get Retrieval Instructions")
    ] = False,
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = BASE_URL,
    realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm")
    ] = "osdu",
    client_id: Annotated[str, typer.Option(help="ClientID")] = "osdu-admin",
):
    """
    Simple OSDU Storage and Dataset record lookup
    """
    base_url = base_url.rstrip("/")
    cimpl_token_refresher = setup(base_url=base_url, realm=realm, client_id=client_id)

    if get_retrieval_instructions:
        dataset_dms_client = DatasetDmsClient(
            dataset_url=base_url + "/api/dataset/v2",
            provider=CLOUD_PROVIDER,
            data_partition_id="osdu",
            token_refresher=cimpl_token_refresher,
        )
        r = dataset_dms_client.get_retrieval_instructions(record_id=record_id)
    else:
        record_client = RecordClient(
            storage_url=base_url + "/api/storage/v2",
            provider=CLOUD_PROVIDER,
            data_partition_id="osdu",
            token_refresher=cimpl_token_refresher,
        )
        r = record_client.get_latest_record(recordId=record_id)

    if r.ok:
        console.print(r.json())
    else:
        error_console.print(f"error {r.status_code}")


@cli.command(rich_help_panel="OSDU Related Commands", hidden=True)
def workflows(
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = BASE_URL,
    realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm")
    ] = "osdu",
    client_id: Annotated[str, typer.Option(help="ClientID")] = "osdu-admin",
):
    """
    Simple OSDU Workflows
    """
    base_url = base_url.rstrip("/")
    cimpl_token_refresher = setup(base_url=base_url, realm=realm, client_id=client_id)

    workflow_client = IngestionWorkflowClient(
        ingestion_workflow_url=base_url + "/api/workflow/v1",
        provider=CLOUD_PROVIDER,
        data_partition_id="osdu",
        token_refresher=cimpl_token_refresher,
    )
    r = workflow_client.get_all_workflows_in_partition()

    if r.ok:
        console.print(r.json())
    else:
        error_console.print(f"error {r.status_code} {r.text}")


def get_info(endpt, base_url=BASE_URL):
    url = base_url + endpt + "/info"
    try:
        r = requests.get(url)
    except requests.exceptions.Timeout:
        error_console.print(f"timeout: {url}")
        return None
    except requests.exceptions.TooManyRedirects:
        error_console.print(f"Too many redirects, check URL: {url}")
        return None
    except requests.exceptions.RequestException as e:
        error_console.print(f"Error {url}: {e}")
        return None
        # raise typer.Exit(1)
    if r.ok:
        return r.json()


@cli.command(rich_help_panel="OSDU Related Commands")
def status(
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = BASE_URL,
):
    """
    Get simple health status of OSDU services
    """
    base_url = base_url.rstrip("/")
    errors = 0
    for endpt in sorted(conf.osdu_end_points):
        r = get_info(conf.osdu_end_points[endpt]["api"], base_url=base_url)
        if r:
            console.print(f":white_check_mark: {endpt.title()}")
        else:
            console.print(f":x: {endpt.title()}")
            errors += 1

    if errors > 4:
        # If more than 4 services down set exit status
        raise typer.Exit(1)


@cli.command(rich_help_panel="OSDU Related Commands")
def info(
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = BASE_URL,
    service: Annotated[
        str, typer.Option("--service", "-s", help="Get info for a service")
    ] = None,
):
    """
    Get OSDU service info
    """
    base_url = base_url.rstrip("/")
    if service:
        if service in conf.osdu_end_points:
            r = get_info(conf.osdu_end_points[service]["api"], base_url=base_url)
            if r:
                console.print(f"{service.title()}:")
                console.print(r)
        else:
            error_console.print(f"Unknown service: {service}")
    else:
        for endpt in sorted(conf.osdu_end_points):
            r = get_info(conf.osdu_end_points[endpt]["api"], base_url=base_url)
            if r:
                console.print(f"{endpt.title()}:")
                console.print(r)


if __name__ == "__main__":
    cli()
