# Keycloak Support

CI Butler also have built-in support for managing users and client ids in keycloak and adding users to groups OSDU.
This can be especially useful to when you need to redeploy your OSDU environment or test as part of a pipeline.

Only some of the capabilities are outlined here.

!!! info "Additional Documentation is Available"
    **CI Butler has built-in help**:

     - `cibutler --help` for overall help
     - `cibutler command --help` for help on a individual command

    There is also a command feference on all the commands and options:

    - See [Command Reference](./commands_reference.md).

## Get an Access Token

To get an access token:

```
cibutler token
```

To get an access token and copy it to your clipboard:

```
cibutler token --clip
```

## Get an Access Token for another user

To be prompted for password for user:

```
cibutler token --username
```

You can also provide the password on command-line via `--password` or via env var `USER_PASSWORD`

## Users

### Get users

```
cibutler list-users
```

### Get users and output as json:

```
cibutler list-users --json > users.json
```

### Import users:

```
cibutler add-users --file users.json
```

If you're not using an export (`list-users --json`).
Here is an example users.json:

```
[
  {
    "username": "jsmith",
    "firstName": "John",
    "lastName": "Smith",
    "email": "john@example.com",
  }
]
```

Optionally if the json includes:
```
    "enabled": true,
    "emailVerified": true,
```

Those values will be used in creation of the accounts, otherwise values for enabled and email verified will be taken from the command-line.  Other values in the json will be ignored.

## Clients

### List clients:

```
cibutler list-clients
```

### Add client

By default clients are created with No Standard flow, No Implict Flow and No Public Client, No Frontchannel logout and No backchannel logout session required, but there are options to enable any of them.

```
cibutler add-client --name client_name
```

