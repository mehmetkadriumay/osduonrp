import os
import requests
import sys
from requests.exceptions import ConnectionError, HTTPError
import typer
from rich.console import Console
from rich.table import Table
from typing import Optional, List
import tenacity
import json
from pathlib import Path
from typing_extensions import Annotated
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
import cibutler.cimpl as cimpl
import cibutler.conf as conf
import cibutler.save as save
import cibutler.utils as utils
import logging

logger = logging.getLogger(__name__)

"""
This limit OSDU functionality is to help verify OSDU is install and working correctly.
It also provides a convenient way to add users.
"""
console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

diag_cli = typer.Typer(
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


@cli.command(rich_help_panel="OSDU Related Commands")
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
        raise typer.Exit(1)


@cli.command(rich_help_panel="OSDU Related Commands")
def legal_tags(
    output: Annotated[
        utils.OutputType, typer.Option("--output", "-o", help="Output style")
    ] = None,
    legal_tag: Annotated[str, typer.Option(help="Legal Tag")] = None,
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = BASE_URL,
    realm: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_REALM", help="Keycloak Realm/OSDU Data Partition ID"
        ),
    ] = "osdu",
    client_id: Annotated[str, typer.Option(help="ClientID")] = "osdu-admin",
    token: Annotated[
        bool,
        typer.Option("--token", envvar="USE_TOKEN", help="Use provided Access Token"),
    ] = False,
    access_token: Annotated[
        str, typer.Option(envvar="TOKEN", help="Access Token")
    ] = None,
):
    """
    Show legal tags

    --legal-tag allows lookup of a single legal tag
    """
    base_url = base_url.rstrip("/")
    if access_token:
        access_token = access_token.strip()

    cimpl_token_refresher = setup(base_url=base_url, realm=realm, client_id=client_id)
    legal_url = base_url + conf.osdu_end_points["legal"]["api"]

    legal_client = LegalClient(
        legal_url=legal_url,
        provider=CLOUD_PROVIDER,
        data_partition_id=realm,
        token_refresher=cimpl_token_refresher,
    )
    try:
        if legal_tag:
            if token:
                r = legal_client.get_legal_tag(
                    legal_tag_name=legal_tag, bearer_token=access_token
                )
            else:
                r = legal_client.get_legal_tag(legal_tag_name=legal_tag)
        else:
            if token:
                r = legal_client.list_legal_tags(bearer_token=access_token)
            else:
                r = legal_client.list_legal_tags()

    except ConnectionError as err:
        error_console.print(f"ConnectionError {legal_url}: {err}")
        raise typer.Exit(1)
    except HTTPError as err:
        error_console.print(f"HTTPError: {err}")
        raise typer.Exit(1)

    if r.ok:
        if output == utils.OutputType.json:
            console.print_json(json.dumps(r.json()))
        elif output == utils.OutputType.excel or output == utils.OutputType.csv:
            save.save_results_pandas(
                data=r.json(),
                output=output,
                record_path="legalTags",
                filename_prefix="legaltags",
            )
        else:
            console.print(r.json())
    else:
        error_console.print(f"Error {legal_url} list_legal_tags: {r.status_code}")
        raise typer.Exit(1)


@cli.command(rich_help_panel="OSDU Related Commands")
def groups(
    output: Annotated[
        utils.OutputType, typer.Option("--output", "-o", help="Output style")
    ] = None,
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = BASE_URL,
    realm: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_REALM", help="Keycloak Realm/OSDU Data Partition ID"
        ),
    ] = "osdu",
    client_id: Annotated[str, typer.Option(help="ClientID")] = "osdu-admin",
    user_id: Annotated[
        str, typer.Option(help="User ID for user with ENTITLEMENTS_IMPERSONATION")
    ] = None,
    token: Annotated[
        bool, typer.Option(envvar="USE_TOKEN", help="Use provided Access Token")
    ] = False,
    access_token: Annotated[
        str, typer.Option(envvar="TOKEN", help="Access Token")
    ] = None,
):
    """
    Groups for current user


    To get groups of another user

    Get an access token for that user
    export TOKEN=`cibutler token --username xyz`

    citbutler groups --token

    User must be a member of service.entitlements.user to use this command (i.e. use entitlements service)
    """
    if access_token:
        access_token = access_token.strip()

    with console.status("Connecting..."):
        base_url = base_url.rstrip("/")
        cimpl_token_refresher = setup(
            base_url=base_url, realm=realm, client_id=client_id
        )
        entitlements_url = base_url + conf.osdu_end_points["entitlements"]["api"]
        entitlement_client = EntitlementsClient(
            entitlements_url=entitlements_url,
            provider=CLOUD_PROVIDER,
            data_partition_id=realm,
            token_refresher=cimpl_token_refresher,
            user_id=user_id,
        )

    try:
        if token and access_token:
            r = entitlement_client.get_groups_for_user(bearer_token=access_token)
        else:
            r = entitlement_client.get_groups_for_user()
    except ConnectionError as err:
        error_console.print(f"ConnectionError: {err}")
        raise typer.Exit(1)
    except HTTPError as err:
        error_console.print(f"HTTPError: {err}")
        raise typer.Exit(1)

    if r.ok:
        if output == utils.OutputType.json:
            console.print_json(json.dumps(r.json()))
        elif output == utils.OutputType.excel or output == utils.OutputType.csv:
            save.save_results_pandas(
                data=r.json(),
                output=output,
                record_path="groups",
                filename_prefix="groups",
            )
        else:
            console.print(r.json())
    else:
        error_console.print(
            f"Error {entitlements_url} get_groups_for_user: {r.status_code}"
        )
        raise typer.Exit(1)


@cli.command(rich_help_panel="OSDU Related Commands")
def group_members(
    output: Annotated[
        utils.OutputType, typer.Option("--output", "-o", help="Output style")
    ] = None,
    group_email: Annotated[
        str, typer.Option("--group-email", "-g", help="Group email to lookup")
    ] = "users@osdu.group",
    role: Annotated[str, typer.Option("--role", "-r", help="Role")] = "MEMBER",
    limit: Annotated[int, typer.Option("--limit", "-l", help="Limit")] = 10,
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = BASE_URL,
    realm: Annotated[
        str,
        typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm/OSDU Partition ID"),
    ] = "osdu",
    client_id: Annotated[str, typer.Option(help="ClientID")] = "osdu-admin",
    token: Annotated[
        bool, typer.Option(envvar="USE_TOKEN", help="Use provided Access Token")
    ] = False,
    access_token: Annotated[
        str, typer.Option(envvar="TOKEN", help="Access Token")
    ] = None,
):
    """
    Get all group members for a given group email
    """
    if access_token:
        access_token = access_token.strip()

    with console.status("Connecting..."):
        base_url = base_url.rstrip("/")
        cimpl_token_refresher = setup(
            base_url=base_url, realm=realm, client_id=client_id
        )
        entitlement_client = EntitlementsClient(
            entitlements_url=base_url + conf.osdu_end_points["entitlements"]["api"],
            provider=CLOUD_PROVIDER,
            data_partition_id=realm,
            token_refresher=cimpl_token_refresher,
        )

    try:
        if token:
            r = entitlement_client.get_group_members(
                group_email=group_email,
                limit=limit,
                role=role,
                bearer_token=access_token,
            )
        else:
            r = entitlement_client.get_group_members(
                group_email=group_email, limit=limit, role=role
            )
    except ConnectionError as err:
        error_console.print(f"ConnectionError: {err}")
        raise typer.Exit(1)
    except HTTPError as err:
        error_console.print(f"HTTPError: {err}")
        raise typer.Exit(1)

    if r.ok:
        if output == utils.OutputType.json:
            console.print_json(json.dumps(r.json()))
        else:
            console.print(r.json())
    else:
        error_console.print(f"Error {r.status_code}")
        raise typer.Exit(1)


@cli.command(rich_help_panel="OSDU Related Commands")
def group_add(
    email: str,
    group_email: Annotated[
        str, typer.Option("--group-email", "-g", help="Group Email")
    ] = "users@osdu.group",
    role: str = "MEMBER",
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = BASE_URL,
    realm: Annotated[
        str,
        typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm/OSDU Partition ID"),
    ] = "osdu",
    client_id: Annotated[str, typer.Option(help="ClientID")] = "osdu-admin",
    token: Annotated[
        bool, typer.Option(envvar="USE_TOKEN", help="Use provided Access Token")
    ] = False,
    access_token: Annotated[
        str, typer.Option(envvar="TOKEN", help="Access Token")
    ] = None,
):
    """
    Add member email to group (create group member)
    """
    add_user_to_group(
        email=email,
        group_email=group_email,
        role=role,
        base_url=base_url,
        realm=realm,
        client_id=client_id,
        token=token,
        access_token=access_token,
    )


@cli.command(rich_help_panel="OSDU Related Commands")
def group_del(
    member_email: str,
    group_email: Annotated[
        str, typer.Option("--group-email", "-g", help="Group Email")
    ] = "users@osdu.group",
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = BASE_URL,
    realm: Annotated[
        str,
        typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm/OSDU Partition ID"),
    ] = "osdu",
    client_id: Annotated[str, typer.Option(help="ClientID")] = "osdu-admin",
    token: Annotated[
        bool, typer.Option(envvar="USE_TOKEN", help="Use provided Access Token")
    ] = False,
    access_token: Annotated[
        str, typer.Option(envvar="TOKEN", help="Access Token")
    ] = None,
):
    """
    Delete member email from group (delete group member)
    """
    del_user_in_group(
        member_email=member_email,
        group_email=group_email,
        base_url=base_url,
        realm=realm,
        client_id=client_id,
        token=token,
        access_token=access_token,
    )


def add_user_to_group(
    email: str,
    group_email: str,
    role: str,
    base_url: str,
    realm: str,
    client_id: str,
    token: bool,
    access_token: str,
):
    """
    add user to group
    """
    base_url = base_url.rstrip("/")
    cimpl_token_refresher = setup(base_url=base_url, realm=realm, client_id=client_id)
    entitlement_client = EntitlementsClient(
        entitlements_url=base_url + conf.osdu_end_points["entitlements"]["api"],
        provider=CLOUD_PROVIDER,
        data_partition_id=realm,
        token_refresher=cimpl_token_refresher,
    )

    try:
        if token:
            r = entitlement_client.create_group_member(
                group_email=group_email,
                group_member=GroupMember(email=email, role=role),
                bearer_token=access_token,
            )
        else:
            r = entitlement_client.create_group_member(
                group_email=group_email,
                group_member=GroupMember(email=email, role=role),
            )
    except ConnectionError as err:
        error_console.print(f"ConnectionError: {err}")
        raise typer.Exit(1)
    except HTTPError as err:
        error_console.print(f"HTTPError: {err}")
        raise typer.Exit(1)

    if r.ok:
        console.print(r.json())
    else:
        if r.status_code == 409:
            error_console.print(f"Already exists {r.status_code}")
        else:
            error_console.print(f"Error {r.status_code}")
            raise typer.Exit(1)


def del_user_in_group(
    member_email: str,
    group_email: str,
    base_url: str,
    realm: str,
    client_id: str,
    token: bool,
    access_token: str,
):
    """
    delete user in group
    """
    base_url = base_url.rstrip("/")
    cimpl_token_refresher = setup(base_url=base_url, realm=realm, client_id=client_id)
    entitlement_client = EntitlementsClient(
        entitlements_url=base_url + conf.osdu_end_points["entitlements"]["api"],
        provider=CLOUD_PROVIDER,
        data_partition_id=realm,
        token_refresher=cimpl_token_refresher,
    )

    try:
        if token:
            r = entitlement_client.delete_group_member(
                group_email=group_email,
                member_email=member_email,
                bearer_token=access_token,
            )
        else:
            r = entitlement_client.delete_group_member(
                group_email=group_email,
                member_email=member_email,
            )
    except ConnectionError as err:
        error_console.print(f"ConnectionError: {err}")
        raise typer.Exit(1)
    except HTTPError as err:
        error_console.print(f"HTTPError: {err}")
        raise typer.Exit(1)

    if r.ok:
        console.print(r.json())
    else:
        error_console.print(f"Error {r.status_code} {r.text}")
        raise typer.Exit(1)


@cli.command(rich_help_panel="OSDU Related Commands")
def groups_add(
    email_list: List[str],
    file: Annotated[Optional[Path], typer.Option("--file", "-f")] = None,
    role: str = "MEMBER",
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = BASE_URL,
    realm: Annotated[
        str,
        typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm/OSDU Partition ID"),
    ] = "osdu",
    client_id: Annotated[str, typer.Option(help="ClientID")] = "osdu-admin",
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview action")] = False,
    token: Annotated[
        bool, typer.Option(envvar="USE_TOKEN", help="Use provided Access Token")
    ] = False,
    access_token: Annotated[
        str, typer.Option(envvar="TOKEN", help="Access Token")
    ] = None,
):
    """
    Utility for adding user(s) to multiple groups

    Example JSON:

    Save groups of a user:
    cibutler groups -o json > groups.json

    Load groups:
    cibutler groups-add --file groups.json user@example.com ...

    Groups can also be loaded from stdin:
    some-command | cibutler groups-add --file - user@example.com ...

    Or all together:
    cibutler groups -o json | cibutler groups-add --file - user@example.com ...
    """

    if access_token:
        access_token = access_token.strip()

    if file is None:
        error_console.print("No file")
        raise typer.Abort()
    elif str(file) == "-":
        file_data = sys.stdin.read().strip()
    elif file.is_file():
        file_data = file.read_text()
    elif file.is_dir():
        error_console.print("path is a directory, not yet supported")
        raise typer.Abort()
    elif not file.exists():
        error_console.print("The file doesn't exist")
        raise typer.Abort()

    try:
        data = json.loads(file_data)
    except json.decoder.JSONDecodeError as err:
        error_console.print(f"JSON validation error: {err}")
        raise typer.Exit(2)

    if "groups" not in data:
        error_console.print("JSON doesn't have groups definition")
        raise typer.Exit(2)

    for email in email_list:
        for group in data["groups"]:
            group_email = group["email"]
            with console.status(f"Adding user to {group_email}..."):
                if dry_run:
                    console.print(f"Would {email} add {group_email}")
                else:
                    add_user_to_group(
                        email=email,
                        group_email=group_email,
                        role=role,
                        base_url=base_url,
                        realm=realm,
                        client_id=client_id,
                        token=token,
                        access_token=access_token,
                    )


@cli.command(rich_help_panel="OSDU Related Commands")
def search(
    output: Annotated[
        utils.OutputType, typer.Option("--output", "-o", help="Output style")
    ] = None,
    kind: Annotated[str, typer.Option(help="Search kind")] = "*:*:*:*",
    query: Annotated[str, typer.Option(help="Search query")] = "",
    limit: Annotated[int, typer.Option(help="Limit results")] = 10,
    offset: Annotated[int, typer.Option(help="Search offset")] = 0,
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = BASE_URL,
    realm: Annotated[
        str,
        typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm/OSDU Partition ID"),
    ] = "osdu",
    client_id: Annotated[str, typer.Option(help="ClientID")] = "osdu-admin",
    token: Annotated[
        bool, typer.Option(envvar="USE_TOKEN", help="Use provided Access Token")
    ] = False,
    access_token: Annotated[
        str, typer.Option(envvar="TOKEN", help="Access Token")
    ] = None,
):
    """
    Simple OSDU Search

    Output as json:
    cibutler search -o json

    Output as excel:
    cibutler search -o excel

    Output as csv:
    cibutler search -o csv

    Output as human readible:
    cibutler search -o human

    Example Searches:
    Wellbore Master Data Instances for Well with ID 1691:
    --kind="*:*:master-data--Wellbore:*" --query=data.WellID:\\"osdu:master-data--Well:1691:\\"

    Wellbore Trajectory Work Product Components associated with Wellbore ID 1691:
    --kind="*:*:work-product-component--WellboreTrajectory:*" --query=data.WellboreID:\\"osdu:master-data--Wellbore:1691:\\"

    Any record with any field equal "well":
    --kind="*:*:*:*" --query=well

    Where source is blended or TNO:
    --kind="*:*:*:*" --query="data.Source:(BLENDED TNO)"

    Where source is exactly "TNO":
    --kind="*:*:*:*" --query=data.Source:\\"TNO\\"

    All wellbore logs from 2022 year:
    --kind="*:*:work-product-component--WellLog:*" --query="createTime:[2022-01-01 TO 2022-12-31]"

    All well logs deeper than 4000m:
    --kind="*:*:work-product-component--WellLog:*" --query="data.BottomMeasuredDepth:[4000 TO *]"

    All well logs deeper than 2000m or shallower than 4000m:
    --kind="*:*:work-product-component--WellLog:*" --query="data.BottomMeasuredDepth:(>=2000 OR <=4000)"
    """
    if access_token:
        access_token = access_token.strip()

    base_url = base_url.rstrip("/")
    cimpl_token_refresher = setup(base_url=base_url, realm=realm, client_id=client_id)
    search_client = SearchClient(
        search_url=base_url + conf.osdu_end_points["search"]["api"],
        provider=CLOUD_PROVIDER,
        data_partition_id=realm,
        token_refresher=cimpl_token_refresher,
    )

    query_request = QueryRequest(kind=kind, query=query, limit=limit, offset=offset)
    try:
        if token:
            r = search_client.query_records(
                query_request=query_request,
                bearer_token=access_token,
            )
        else:
            r = search_client.query_records(
                query_request=query_request,
            )
    except ConnectionError as err:
        error_console.print(f"ConnectionError: {err}")
        raise typer.Exit(1)
    except HTTPError as err:
        error_console.print(f"HTTPError: {err}")
        raise typer.Exit(1)

    if r.ok:
        if output == utils.OutputType.json:
            console.print_json(json.dumps(r.json()))
        else:
            count = 0
            if "results" in r.json():
                count = len(r.json()["results"])

            if output == utils.OutputType.human:
                display_search_results_human(r.json())
            elif output == utils.OutputType.excel or output == utils.OutputType.csv:
                save.save_results_pandas(
                    data=r.json(), output=output, filename_prefix="search"
                )
            else:
                console.print(r.json())

    else:
        error_console.print(f"Search error {r.status_code}")
        raise typer.Exit(1)


def display_search_results_human(data, show_kind=False):
    count = len(data["results"])
    if not count:
        return
    table = Table(title=f"Search Results ({count})")
    table.add_column("ID", justify="full", style="cyan", no_wrap=True, min_width=25)
    if show_kind:
        table.add_column(
            "Kind", justify="full", style="cyan", no_wrap=True, min_width=25
        )
    table.add_column(
        "Authority", justify="center", style="green", no_wrap=True, max_width=10
    )
    table.add_column(
        "Source", justify="center", style="green", no_wrap=True, max_width=8
    )
    table.add_column(
        "Type", justify="center", style="green", no_wrap=True, min_width=15
    )
    table.add_column(
        "Created", justify="center", style="green", no_wrap=True, max_width=11
    )

    for item in data["results"]:
        created = item["createTime"]
        if show_kind:
            table.add_row(
                item["id"],
                item["kind"],
                item["authority"],
                item["source"],
                item["type"],
                created,
            )
        else:
            table.add_row(
                item["id"], item["authority"], item["source"], item["type"], created
            )
    console.print(table)


@cli.command(rich_help_panel="OSDU Related Commands")
def record(
    record_id: Annotated[str, typer.Argument(help="Storage Record")],
    output: Annotated[
        utils.OutputType, typer.Option("--output", "-o", help="Output style")
    ] = None,
    get_retrieval_instructions: Annotated[
        bool,
        typer.Option(
            "--get-retrieval-instructions", "-r", help="Get Retrieval Instructions"
        ),
    ] = False,
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = BASE_URL,
    realm: Annotated[
        str,
        typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm/OSDU Partition ID"),
    ] = "osdu",
    client_id: Annotated[str, typer.Option(help="ClientID")] = "osdu-admin",
    token: Annotated[
        bool, typer.Option(envvar="USE_TOKEN", help="Use provided Access Token")
    ] = False,
    access_token: Annotated[
        str, typer.Option(envvar="TOKEN", help="Access Token")
    ] = None,
):
    """
    Simple OSDU Storage and Dataset record lookup
    """
    if access_token:
        access_token = access_token.strip()

    base_url = base_url.rstrip("/")
    cimpl_token_refresher = setup(base_url=base_url, realm=realm, client_id=client_id)

    if get_retrieval_instructions:
        dataset_dms_client = DatasetDmsClient(
            dataset_url=base_url + conf.osdu_end_points["dataset"]["api"],
            provider=CLOUD_PROVIDER,
            data_partition_id=realm,
            token_refresher=cimpl_token_refresher,
        )
        try:
            if token:
                r = dataset_dms_client.get_retrieval_instructions(
                    record_id=record_id,
                    bearer_token=access_token,
                )
            else:
                r = dataset_dms_client.get_retrieval_instructions(record_id=record_id)

        except ConnectionError as err:
            error_console.print(f"ConnectionError: {err}")
            raise typer.Exit(1)
        except HTTPError as err:
            error_console.print(f"HTTPError: {err}")
            raise typer.Exit(1)
    else:
        record_client = RecordClient(
            storage_url=base_url + conf.osdu_end_points["storage"]["api"],
            provider=CLOUD_PROVIDER,
            data_partition_id=realm,
            token_refresher=cimpl_token_refresher,
        )

        try:
            if token:
                r = record_client.get_latest_record(
                    recordId=record_id,
                    bearer_token=access_token,
                )
            else:
                r = record_client.get_latest_record(recordId=record_id)
        except ConnectionError as err:
            error_console.print(f"ConnectionError: {err}")
            raise typer.Exit(1)
        except HTTPError as err:
            error_console.print(f"HTTPError: {err}")
            raise typer.Exit(1)

    if r.ok:
        if output == utils.OutputType.json:
            console.print_json(json.dumps(r.json()))
        elif output == utils.OutputType.excel or output == utils.OutputType.csv:
            save.save_results_pandas(
                data=r.json(), output=output, filename_prefix="record", record_path=None
            )
        else:
            console.print(r.json())
    else:
        error_console.print(f"error {r.status_code}")
        raise typer.Exit(1)


@cli.command(rich_help_panel="OSDU Related Commands")
def workflows(
    output: Annotated[
        utils.OutputType, typer.Option("--output", "-o", help="Output style")
    ] = None,
    base_url: Annotated[
        str, typer.Option(envvar="BASE_URL", help="BASE URL for OSDU")
    ] = BASE_URL,
    realm: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_REALM", help="Keycloak Realm/OSDU Data Partition ID"
        ),
    ] = "osdu",
    client_id: Annotated[str, typer.Option(help="ClientID")] = "osdu-admin",
    token: Annotated[
        bool, typer.Option(envvar="USE_TOKEN", help="Use provided Access Token")
    ] = False,
    access_token: Annotated[
        str, typer.Option(envvar="TOKEN", help="Access Token")
    ] = None,
):
    """
    Simple OSDU Workflows
    """
    if access_token:
        access_token = access_token.strip()

    base_url = base_url.rstrip("/")
    cimpl_token_refresher = setup(base_url=base_url, realm=realm, client_id=client_id)

    workflow_client = IngestionWorkflowClient(
        ingestion_workflow_url=base_url + conf.osdu_end_points["workflow"]["api"],
        provider=CLOUD_PROVIDER,
        data_partition_id=realm,
        token_refresher=cimpl_token_refresher,
    )

    try:
        if token:
            r = workflow_client.get_all_workflows_in_partition(
                bearer_token=access_token,
            )
        else:
            r = workflow_client.get_all_workflows_in_partition()
    except ConnectionError as err:
        error_console.print(f"ConnectionError: {err}")
        raise typer.Exit(1)
    except HTTPError as err:
        error_console.print(f"HTTPError: {err}")
        raise typer.Exit(1)

    if r.ok:
        if output == utils.OutputType.json:
            console.print_json(json.dumps(r.json()))
        elif output == utils.OutputType.excel or output == utils.OutputType.csv:
            save.save_results_pandas(
                data=r.json(),
                output=output,
                filename_prefix="workflows",
                record_path=None,
            )
        else:
            console.print(r.json())
    else:
        error_console.print(f"error {r.status_code} {r.text}")
        raise typer.Exit(1)


def get_info(endpt, base_url=BASE_URL, timeout=5):
    url = base_url + endpt + "/info"
    try:
        r = requests.get(url, timeout=timeout)
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
    threshold: Annotated[int, typer.Option(help="Threshold for exit status")] = 1,
    timeout: Annotated[int, typer.Option(help="Timeout")] = 5,
):
    """
    Get simple health status of OSDU services

    The threshold is for providing an exit status
    if the number of services down/giving an error is greater or equal to that number
    than a non-zero exit status will be given
    """
    base_url = base_url.rstrip("/")
    errors = 0
    for endpt in sorted(conf.osdu_end_points):
        r = get_info(
            conf.osdu_end_points[endpt]["api"], base_url=base_url, timeout=timeout
        )
        if r:
            console.print(f":white_check_mark: {endpt.title()}")
        else:
            console.print(f":x: {endpt.title()}")
            errors += 1

    if errors >= threshold:
        raise typer.Exit(errors)


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
