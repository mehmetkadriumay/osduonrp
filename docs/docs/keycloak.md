# Keycloak

CI Butler also have built-in support for managing users and client ids in keycloak and adding users to groups OSDU.
This can be especially useful to when you need to redeploy your OSDU environment or test as part of a pipeline.

Here are some of the capabilities:

## Get an Access Token

`cibutler token`

## Users

Get users:

`cibutler list-users`

Get users and output as json:

`cibutler list-users --json > users.json`

Import users:

`cibutler add-users --file users.json`

## Clients

List clients:

`cibutler list-clients`

Add client. By default clients are created with No Standard flow, No Implict Flow and No Public Client, No Frontchannel logout and No backchannel logout session required, but there are options to enable any of them.

`cibutler add-client --name client_name`

For more information on these and other options:
- `cibutler --help`
- `cibutler command --help`
- See [command reference](./commands_reference.md)