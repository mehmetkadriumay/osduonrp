#!/usr/bin/env python3.11
import typer
from typing_extensions import Annotated
from rich.console import Console
from keycloak import KeycloakAdmin
from keycloak import KeycloakOpenIDConnection
import keycloak.exceptions
import requests
import pyperclip
import cibutler.cimpl as cimpl

console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

KEYCLOAK_URL = "http://keycloak.localhost/"


@cli.command(rich_help_panel="Keycloak Related Commands")
def token(
    clip: Annotated[bool, typer.Option(help="Copy Access token to clipboard")] = False,
    realm: Annotated[
        str,
        typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm/Data Partition ID"),
    ] = "osdu",
    detail: Annotated[bool, typer.Option("--all", help="Display Details")] = False,
    client_id: Annotated[str, typer.Option(help="Client ID")] = "osdu-admin",
    client_secret: Annotated[str, typer.Option(help="Client ID")] = None,
    base_url: Annotated[
        str, typer.Option(envvar="KEYCLOAK_URL", help="BASE URL for keycloak")
    ] = KEYCLOAK_URL,
):
    """
    Get Access Bearer token from keycloak
    """
    if not client_secret:
        client_secret = cimpl.get_keycloak_client_secret()

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "email openid profile",
    }
    try:
        r = requests.post(
            url=f"{base_url}/realms/{realm}/protocol/openid-connect/token",
            data=data,
        )
    except requests.exceptions.ConnectionError:
        error_console.print("Unable to connect to keycloak. Is tunnel running?")
        raise typer.Exit(1)

    if r.ok:
        if detail:
            console.print(r.json())
        else:
            console.print(r.json()["access_token"])

        if clip:
            pyperclip.copy(r.json()["access_token"])

    else:
        console.print(f"error {r.status_code}")


@cli.command(rich_help_panel="Keycloak Related Commands")
def list_clients(
    admin_user: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_ADMIN", help="Admin User to authenticate to Keycloak"
        ),
    ] = "user",
    admin_password: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_ADMIN_PASSWORD",
            help="Admin Password to authenticate to Keycloak",
        ),
    ] = None,
    base_url: Annotated[
        str, typer.Option(envvar="KEYCLOAK_URL", help="BASE URL for keycloak")
    ] = KEYCLOAK_URL,
    realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm")
    ] = "osdu",
    user_realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak User Realm")
    ] = "master",
):
    """
    List all clients in keycloak.

    If no admin password is provided will use password from bootstrapping
    """
    if not admin_password:
        admin_password = cimpl.get_keycloak_admin_password()

    keycloak_connection = KeycloakOpenIDConnection(
        server_url=base_url,
        username=admin_user,
        password=admin_password,
        realm_name=realm,
        user_realm_name=user_realm,
        verify=True,
    )

    try:
        keycloak_admin = KeycloakAdmin(connection=keycloak_connection)
        clients = keycloak_admin.get_clients()
    except keycloak.KeycloakAuthenticationError as err:
        error_console.print(f"Authentication Error {err}")
        raise typer.Exit(1)
    except keycloak.KeycloakConnectionError as err:
        error_console.print(f"Connection Error: {err}")
        raise typer.Exit(1)
    console.print(clients)


@cli.command(rich_help_panel="Keycloak Related Commands")
def add_client(
    client_id: Annotated[
        str,
        typer.Argument(help="Client ID to add"),
    ],
    name: Annotated[
        str,
        typer.Option(help="Client ID to add"),
    ] = "",
    exists_ok: bool = False,
    standard_flow_enabled: Annotated[bool, typer.Option(help="Standard Flow")] = False,
    implicit_flow_enabled: Annotated[bool, typer.Option(help="Implicit Flow")] = False,
    public_client: Annotated[bool, typer.Option(help="Public Client")] = False,
    frontchannel_logout: Annotated[
        bool, typer.Option(help="Front channel Logout")
    ] = False,
    backchannel_logout_session_required: Annotated[
        bool, typer.Option(help="Backchannel logout session required")
    ] = False,
    admin_user: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_ADMIN", help="Admin User to authenticate to Keycloak"
        ),
    ] = "user",
    admin_password: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_ADMIN_PASSWORD",
            help="Admin Password to authenticate to Keycloak",
        ),
    ] = None,
    base_url: Annotated[
        str, typer.Option(envvar="KEYCLOAK_URL", help="BASE URL for keycloak")
    ] = KEYCLOAK_URL,
    realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm")
    ] = "osdu",
    user_realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak User Realm")
    ] = "master",
):
    """
    Add client in keycloak.

    If no admin password is provided will use password from bootstrapping
    """
    if not admin_password:
        admin_password = cimpl.get_keycloak_admin_password()

    keycloak_connection = KeycloakOpenIDConnection(
        server_url=base_url,
        username=admin_user,
        password=admin_password,
        realm_name=realm,
        user_realm_name=user_realm,
        verify=True,
    )
    # https://www.keycloak.org/docs-api/latest/rest-api/index.html#ClientRepresentation
    payload = {
        # "protocol": "openid-connect",
        "name": name,
        "clientId": client_id,
        "enabled": True,
        "standardFlowEnabled": standard_flow_enabled,
        "implicitFlowEnabled": implicit_flow_enabled,
        "authorizationServicesEnabled": True,
        "publicClient": public_client,
        "directAccessGrantsEnabled": True,
        "serviceAccountsEnabled": True,
        "frontchannelLogout": frontchannel_logout,
        "attributes": {
            "backchannel.logout.session.required": backchannel_logout_session_required
        },
    }

    keycloak_admin = KeycloakAdmin(connection=keycloak_connection)
    try:
        cid = keycloak_admin.create_client(payload=payload, skip_exists=exists_ok)
    except keycloak.exceptions.KeycloakPostError as err:
        error_console.print(f"Unable to add client {client_id}! {err}")
        raise typer.Exit(1)
    except keycloak.KeycloakAuthenticationError as err:
        error_console.print(f"Authentication Error {err}")
        raise typer.Exit(1)
    except keycloak.KeycloakConnectionError as err:
        error_console.print(f"Connection Error: {err}")
        raise typer.Exit(1)

    if cid:
        client_detail = keycloak_admin.get_client(cid)
        console.print(
            f"Client ID: {client_detail['clientId']}\nClient Secret: {client_detail['secret']}"
        )


@cli.command(rich_help_panel="Keycloak Related Commands")
def list_users(
    admin_user: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_ADMIN", help="Admin User to authenticate to Keycloak"
        ),
    ] = "user",
    admin_password: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_ADMIN_PASSWORD",
            help="Admin Password to authenticate to Keycloak",
        ),
    ] = None,
    base_url: Annotated[
        str, typer.Option(envvar="KEYCLOAK_URL", help="BASE URL for keycloak")
    ] = KEYCLOAK_URL,
    realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm")
    ] = "osdu",
    user_realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak User Realm")
    ] = "master",
):
    """
    List all users in keycloak.

    If no admin password is provided will use password from bootstrapping
    """
    if not admin_password:
        admin_password = cimpl.get_keycloak_admin_password()

    keycloak_connection = KeycloakOpenIDConnection(
        server_url=base_url,
        username=admin_user,
        password=admin_password,
        realm_name=realm,
        user_realm_name=user_realm,
        verify=True,
    )

    try:
        keycloak_admin = KeycloakAdmin(connection=keycloak_connection)
        users = keycloak_admin.get_users({})
    except keycloak.KeycloakAuthenticationError as err:
        error_console.print(f"Authentication Error {err}")
        raise typer.Exit(1)
    except keycloak.KeycloakConnectionError as err:
        error_console.print(f"Connection Error: {err}")
        raise typer.Exit(1)

    console.print(users)


@cli.command(rich_help_panel="Keycloak Related Commands", hidden=True)
def get_user_id(
    username: Annotated[str, typer.Argument(help="Username")],
    admin_user: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_ADMIN", help="Admin User to authenticate to Keycloak"
        ),
    ] = "user",
    admin_password: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_ADMIN_PASSWORD",
            help="Admin Password to authenticate to Keycloak",
        ),
    ] = None,
    base_url: Annotated[
        str, typer.Option(envvar="KEYCLOAK_URL", help="BASE URL for keycloak")
    ] = KEYCLOAK_URL,
    realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm")
    ] = "osdu",
    user_realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak User Realm")
    ] = "master",
):
    """
    Get internal keycloak user-id for a user
    """
    if not admin_password:
        admin_password = cimpl.get_keycloak_admin_password()

    keycloak_connection = KeycloakOpenIDConnection(
        server_url=base_url,
        username=admin_user,
        password=admin_password,
        realm_name=realm,
        user_realm_name=user_realm,
        verify=True,
    )

    try:
        keycloak_admin = KeycloakAdmin(connection=keycloak_connection)
        detail = keycloak_admin.get_user_id(username)
    except keycloak.KeycloakAuthenticationError as err:
        error_console.print(f"Authentication Error {err}")
        raise typer.Exit(1)
    except keycloak.KeycloakConnectionError as err:
        error_console.print(f"Connection Error: {err}")
        raise typer.Exit(1)
    console.print(detail)


@cli.command(rich_help_panel="Keycloak Related Commands", hidden=True)
def get_client_id(
    client_id: Annotated[str, typer.Argument(help="Client ID")],
    admin_user: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_ADMIN", help="Admin User to authenticate to Keycloak"
        ),
    ] = "user",
    admin_password: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_ADMIN_PASSWORD",
            help="Admin Password to authenticate to Keycloak",
        ),
    ] = None,
    base_url: Annotated[
        str, typer.Option(envvar="KEYCLOAK_URL", help="BASE URL for keycloak")
    ] = KEYCLOAK_URL,
    realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm")
    ] = "osdu",
    user_realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak User Realm")
    ] = "master",
):
    """
    Get internal keycloak user-id for a user
    """
    if not admin_password:
        admin_password = cimpl.get_keycloak_admin_password()

    keycloak_connection = KeycloakOpenIDConnection(
        server_url=base_url,
        username=admin_user,
        password=admin_password,
        realm_name=realm,
        user_realm_name=user_realm,
        verify=True,
    )

    try:
        keycloak_admin = KeycloakAdmin(connection=keycloak_connection)
        detail = keycloak_admin.get_client_id(client_id)
    except keycloak.KeycloakAuthenticationError as err:
        error_console.print(f"Authentication Error {err}")
        raise typer.Exit(1)
    except keycloak.KeycloakConnectionError as err:
        error_console.print(f"Connection Error: {err}")
        raise typer.Exit(1)
    console.print(detail)


@cli.command(rich_help_panel="Keycloak Related Commands")
def client_id(
    client_id: Annotated[str, typer.Argument(help="Client ID")],
    secret: Annotated[
        bool,
        typer.Option(help="Get Secret for client_id"),
    ] = False,
    admin_user: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_ADMIN", help="Admin User to authenticate to Keycloak"
        ),
    ] = "user",
    admin_password: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_ADMIN_PASSWORD",
            help="Admin Password to authenticate to Keycloak",
        ),
    ] = None,
    base_url: Annotated[
        str, typer.Option(envvar="KEYCLOAK_URL", help="BASE URL for keycloak")
    ] = KEYCLOAK_URL,
    realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm")
    ] = "osdu",
    user_realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak User Realm")
    ] = "master",
):
    """
    Get client details
    """
    if not admin_password:
        admin_password = cimpl.get_keycloak_admin_password()

    keycloak_connection = KeycloakOpenIDConnection(
        server_url=base_url,
        username=admin_user,
        password=admin_password,
        realm_name=realm,
        user_realm_name=user_realm,
        verify=True,
    )

    try:
        keycloak_admin = KeycloakAdmin(connection=keycloak_connection)
        internal_client_id = keycloak_admin.get_client_id(client_id)
        details = keycloak_admin.get_client(internal_client_id)
    except keycloak.KeycloakAuthenticationError as err:
        error_console.print(f"Authentication Error {err}")
        raise typer.Exit(1)
    except keycloak.KeycloakConnectionError as err:
        error_console.print(f"Connection Error: {err}")
        raise typer.Exit(1)

    if secret:
        console.print(details["secret"])
    else:
        console.print(details)


@cli.command(rich_help_panel="Keycloak Related Commands")
def add_user(
    email: Annotated[str, typer.Argument(help="Email address")],
    username: Annotated[str, typer.Argument(help="Username")],
    first: Annotated[str, typer.Argument(help="First Name")],
    last: Annotated[str, typer.Argument(help="Last Name")],
    admin_password: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_ADMIN_PASSWORD",
            help="Admin Password to authenticate to Keycloak",
        ),
    ] = None,
    enabled: Annotated[
        bool, typer.Option("--enabled/--disabled", help="Make User Enabled")
    ] = True,
    email_verified: Annotated[bool, typer.Option(help="Make User Enabled")] = True,
    exists_ok: Annotated[bool, typer.Option(help="Okay if user already exists")] = True,
    admin_user: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_ADMIN", help="Admin User to authenticate to Keycloak"
        ),
    ] = "user",
    base_url: Annotated[
        str, typer.Option(envvar="KEYCLOAK_URL", help="BASE URL for keycloak")
    ] = KEYCLOAK_URL,
    realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm")
    ] = "osdu",
    user_realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak User Realm")
    ] = "master",
):
    """
    Add/Update a user in keycloak
    """
    if not admin_password:
        admin_password = cimpl.get_keycloak_admin_password()

    keycloak_connection = KeycloakOpenIDConnection(
        server_url=base_url,
        username=admin_user,
        password=admin_password,
        realm_name=realm,
        user_realm_name=user_realm,
        verify=True,
    )

    try:
        keycloak_admin = KeycloakAdmin(
            connection=keycloak_connection, user_realm_name="osdu"
        )
        new_user = keycloak_admin.create_user(
            {
                "email": email,
                "username": username,
                "enabled": enabled,
                "firstName": first,
                "lastName": last,
                "emailVerified": email_verified,
            },
            exist_ok=exists_ok,
        )
    except keycloak.KeycloakAuthenticationError as err:
        error_console.print(f"Authentication Error {err}")
        raise typer.Exit(1)
    except keycloak.KeycloakConnectionError as err:
        error_console.print(f"Connection Error: {err}")
        raise typer.Exit(1)

    console.print(new_user)


@cli.command(rich_help_panel="Keycloak Related Commands")
def set_user_password(
    username: Annotated[str, typer.Argument(help="Username")],
    password: Annotated[
        str,
        typer.Option(
            prompt=True, confirmation_prompt=True, hide_input=True, help="Password"
        ),
    ],
    temporary: Annotated[bool, typer.Option(help="Make password be temporary")] = False,
    admin_user: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_ADMIN", help="Admin User to authenticate to Keycloak"
        ),
    ] = "user",
    admin_password: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_ADMIN_PASSWORD",
            help="Admin Password to authenticate to Keycloak",
        ),
    ] = None,
    base_url: Annotated[
        str, typer.Option(envvar="KEYCLOAK_URL", help="BASE URL for keycloak")
    ] = KEYCLOAK_URL,
    realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm")
    ] = "osdu",
    user_realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak User Realm")
    ] = "master",
):
    """
    Set user password in Keycloak
    """
    if not admin_password:
        admin_password = cimpl.get_keycloak_admin_password()

    keycloak_connection = KeycloakOpenIDConnection(
        server_url=base_url,
        username=admin_user,
        password=admin_password,
        realm_name=realm,
        user_realm_name=user_realm,
        verify=True,
    )

    try:
        keycloak_admin = KeycloakAdmin(connection=keycloak_connection)
        user_id = keycloak_admin.get_user_id(username)
        if user_id:
            keycloak_admin.set_user_password(
                user_id=user_id, password=password, temporary=temporary
            )
            console.print(f"Pasword set for user: {username} with user_id: {user_id}")
        else:
            error_console.print(f"Unable to lookup user {username}")
    except keycloak.KeycloakAuthenticationError as err:
        error_console.print(f"Authentication Error {err}")
        raise typer.Exit(1)
    except keycloak.KeycloakConnectionError as err:
        error_console.print(f"Connection Error: {err}")
        raise typer.Exit(1)


@cli.command(rich_help_panel="Keycloak Related Commands")
def delete_user(
    username: Annotated[str, typer.Argument(help="Username to delete")],
    admin_user: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_ADMIN", help="Admin User to authenticate to Keycloak"
        ),
    ] = "user",
    admin_password: Annotated[
        str,
        typer.Option(
            envvar="KEYCLOAK_ADMIN_PASSWORD",
            help="Admin Password to authenticate to Keycloak",
        ),
    ] = None,
    base_url: Annotated[
        str, typer.Option(envvar="KEYCLOAK_URL", help="BASE URL for keycloak")
    ] = KEYCLOAK_URL,
    realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak Realm")
    ] = "osdu",
    user_realm: Annotated[
        str, typer.Option(envvar="KEYCLOAK_REALM", help="Keycloak User Realm")
    ] = "master",
):
    """
    Delete user from Keycloak
    """
    if not admin_password:
        admin_password = cimpl.get_keycloak_admin_password()

    keycloak_connection = KeycloakOpenIDConnection(
        server_url=base_url,
        username=admin_user,
        password=admin_password,
        realm_name=realm,
        user_realm_name=user_realm,
        verify=True,
    )

    try:
        keycloak_admin = KeycloakAdmin(connection=keycloak_connection)
        user_id = keycloak_admin.get_user_id(username)
    except keycloak.KeycloakAuthenticationError as err:
        error_console.print(f"Authentication Error {err}")
        raise typer.Exit(1)
    except keycloak.KeycloakConnectionError as err:
        error_console.print(f"Connection Error: {err}")
        raise typer.Exit(1)

    if user_id:
        response = keycloak_admin.delete_user(user_id=user_id)
        console.print(response)


if __name__ == "__main__":
    cli()
