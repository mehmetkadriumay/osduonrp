# Install
## Requirements for using CI Butler and deploying CImpl locally

Currently CI Butler only supports minikube with Docker.
However in future support could be added for: QEMU, Hyperkit, Hyper-V, KVM, Parallels, Podman, VirtualBox, VMware Fusion/Workstation, etc.

!!! info "Install Requirements for installing CImpl locally"

    If you're don't intend to install CImpl locally but are using CI Butler as part of a pipeline or automation these requirements can be ignored.

    - Mac OS, Windows or Linux
    - 150GB of free disk space
    - Min. 32GB of RAM. Limited success and testing with Mac with 24GB of RAM. Hope to test more in the future.
    - 6 logical processors. Limited success with 4 logical processors


## Installation Instructions

### Install and configure prerequisites

If you intend to deploy CImpl locally you'll need the following.

1. Install docker desktop
1. Install helm
1. Install minikube
1. Increase RAM in docker desktop to 24+ GB and restart docker
1. Install uv (or pipx)

### Optional but useful addons
1. install metrics
   `minikube addons enable metrics-server`
   then you can use `minikube dashboard`
1. install k9s
   `brew install derailed/k9s/k9s`

## Install (pre-release) from OSDU gitlab built packages

To install CI Butler we recommend using pipx:
``` bash title="Install CI Butler"
pipx install cibutler --index-url https://community.opengroup.org/api/v4/projects/1558/packages/pypi/simple --pip-args="--extra-index-url=https://community.opengroup.org/api/v4/projects/148/packages/pypi/simple"
```

If you don't already have pipx installed:

To install pipx using pip:

``` bash title="Install pipx"
python -m pip install --user pipx
python -m pipx ensurepath
```
Then restart your terminal/shell so that pipx will be in your path.

## Pre CI Impl Preflight check

```
cibutler check
```

## Install CImpl

CI Butler will attempt to make educated guesses on how much RAM and CPU to give OSDU based upon settings in Docker and the hardware that you have.

```
cibutler install
```

If you want to ignore these recommendations (especially useful if you have less CPU or RAM than required):

```
cibutler install --max-cpu --max-memory
```

If you want to have a install data loading and not have to select it later:

```
cibutler install --data-load-flag=tno-volve-reference
```

If you want to have a fully automated install without data loading:

```
cibutler install --data-load-flag=skip --quiet
```

## Confirm things are working

### Tunnel

One of the following:

```
cibutler tunnel
```
Alternatively you can run `minikube tunnel`.

### Get access/refresh tokens

Get access token:
```
cibutler token
```

Get refresh token:
```
cibutler refresh-token
```

Or Curl command
``` bash title="Curl to get access token"
curl --location 'http://keycloak.localhost/realms/osdu/protocol/openid-connect/token' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode 'grant_type=client_credentials' \
--data-urlencode 'client_id=osdu-admin' \
--data-urlencode 'client_secret=your-client-secret' \
--data-urlencode 'scope=email openid profile'
```

### Status

```
cibutler status
```

### Get client_secret:

One of the following:

```
cibutler client-secret
```
alternatively you can run kubectl directly:

`kubectl get secret keycloak-bootstrap-secret -o jsonpath="{.data.KEYCLOAK_OSDU_ADMIN_SECRET}" | base64 --decode`

### Fetch the WellboreTrajectory 1.1.0 schema:

There isn't a built-in cibutler command for this
``` bash title="Curl to get schema"
curl --location 'http://osdu.localhost/api/schema-service/v1/schema/osdu:wks:work-product-component--WellboreTrajectory:1.1.0' \
--header 'Content-Type: application/json' \
--header 'data-partition-id: osdu' \
--header 'Authorization: Bearer <access_token_here>'
```

## Data loading

By default `cibutler install` will not exit until data loading is completed. However you can also check that data loading finished by running:

```
kubectl get po | grep bootstrap-data
```

Or use K9s to check on the pod status
When pods in Ready column will look like "1/1" the process is finished.

## Delete / Uninstall

To completely remove CImpl run one of the following:

- `cibutler delete`
- `minikube delete`