# OSDU Related Commands

CI Butler also has built-in support for various OSDU functionality, in particular for automation and testing needs.

This can be especially useful to when you need to redeploy your OSDU environment or test as part of a pipeline.

Only some of the capabilities are outlined here. There are more commands and options.

!!! question "Additional Documentation is Available"
    **CI Butler has great built-in help**:

     - `cibutler --help` for overall help
     - `cibutler command --help` for help on a individual command

    There is also a command feference on all the commands and options:

    - See [Command Reference](./commands_reference.md).


!!! tip "Output Formats"

    Some commands support different output formats.
    These may include human, json, csv and excel formats.

## Get Legal Tags

Get all legal tags:
```
cibutler legal-tags
```

Get a single legal tag
```
cibutler legal-tags --legal-tag osdu-default-data-tag
```

To get output in json format add `-o json`

## Get Groups

```
cibutler groups
```

To get groups of another user provide Bearer Access Token via env var `TOKEN` or `--access-token`.
```
cibutler groups --token
```
To get access token of another user [Keycloak token](./keycloak.md#get-an-access-token-for-another-user)

To get output in json format add `-o json`, for example:
```
cibutler groups -o json > groups.json
```

## Get Group Members

To get members of a group, provide the group email
```
cibutler group-members -g users@osdu.group
```
To get output in json format add `-o json`

## Add a member to Group

To add a member email to a group aka Create Group Member

```
cibutler group-add user@example.com -g users@osdu.group
```

## Add a member(s) to Groups in Batch

This command is for adding a number of groups to a user.

The groups.json file or input must be in the format:
```
{
  "groups": [
    {
      "name": "service.fetch.viewers",
      "description": "Fetch viewers group",
      "email": "service.fetch.viewers@osdu.group"
    },
    {
      ...
    }
  ]
}
```
It may contain other things only groups["email] will to used.

To obtain a list of groups in this format see [groups command](osdu.md#get-groups)

```
cibutler groups-add -f groups.json user@example.com
```

Alternatively groups-add can read from stdin
```
cibutler groups -o json | cibutler groups-add -f - user@example.com
```

You can also provide a list of users
```
cibutler groups-add -f groups.json user1@example.com user2@example.com user3@example.com ...
```

If user is already part of group you will get a warning and then continue on.

## Delete a member from Group

```
cibutler group-del -g user-group@osdu.group user@example.com
```

Please note a user cannot be removed from elementary data partition group if they are provisioned inside other groups. Group hierarchy is preserved.

## Search

Basis search to check for data

Basic search in human printed format
```
cibutler search -o human
```

Output in json:
```
cibutler search -o json
```

Output in csv:
```
cibutler search -o csv
```

Output in excel:
```
cibutler search -o excel
```

You can of course provide expected options:
- `--kind` default is `*.*.*.*`
- `--query`
- `--limit` default is 10
- `--offset` default is 0

## Record

Get details on a single record
```
cibutler record osdu:reference-data--ActivityCode:hor_ds_cs_cw_wcic
```

## Status

Get status on OSDU services
```
cibutler status
```

If services are down or unavailble a non-zero exit status will be given.
By default this threshold for checking services being down is 1 or more.
This can be changed via `--threshold` option.

## Info

To get info on all services
```
cibutler info
```

To get info on a single service
```
cibutler info -s storage
```

## Postman Env File

To get a postman environment file (if there is one provided via config `/api/config/v1/postman-environment`) for your deployment:
```
cibutler envfile
```