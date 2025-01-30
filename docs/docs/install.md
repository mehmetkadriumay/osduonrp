# Install
## Requirements for using CI Butler and deploying CImpl locally

Currently CI Butler only supports minikube with Docker.
However in future support could be added for deploying to kubernetes directly as well as minikube in: QEMU, Hyperkit, Hyper-V, KVM, Parallels, Podman, VirtualBox, VMware Fusion/Workstation, etc.
If you're interested in one of these please open an [issue](https://community.opengroup.org/osdu/ui/cibutler/-/issues/) to request it.

!!! info "Install Requirements for installing CImpl locally"

    If you're don't intend to install CImpl locally but are using CI Butler as part of a pipeline or automation these requirements can be ignored.

    - Mac OS, Windows or Linux
    - 150GB of free disk space
    - Min. 32GB of RAM. Limited success and testing with Mac with 24GB of RAM. Hope to test more in the future.
    - 6 logical processors. Limited success with 4 logical processors

## Installation Instructions

### Install and configure prerequisites

``` mermaid
graph LR
  A[Install Python] --> |Installed| B{Install Pipx};
  B -->|Installed| C[Install CI Butler using Pipx];
  C -->|Installed| D[Will you be deploying CImpl locally?];
  D -->|Yes| E[Verify Additional Prerequisites by running cibutler check];
  E -->|Yes| F;
  D ---->|No| F[Installed!];
```

If you intend to deploy CImpl locally you'll need the following:

- Install docker desktop
- Install helm
- Install minikube
- Install kubectl if not already included in the above (docker desktop normally includes it). CIButler attempts to be a pure python implementation but uses both APIs and `kubectl` to configure and deploy to kubernetes.
- Increase RAM in docker desktop to 24+ GB and restart docker
- Increase CPU limit in docker desktop to 6 or more cores. For the best performance setting it to the number of high performance cores is recommended.
- Install Python3.11 or later.
- Install pipx.

### How to install Pipx

If you don't already have pipx installed see [Pipx install guide](https://pipx.pypa.io/latest/installation/)

Here are some options:

   ``` bash title="To install Pipx using pip"
   python -m pip install --user pipx
   python -m pipx ensurepath
   ```

   ``` bash title="To install Pipx using brew on MacOS"
   brew install pipx
   pipx ensurepath
   ```

   ``` title="On Windows install via Scoop"
   scoop install pipx
   pipx ensurepath
   ```

   Then restart your terminal/shell so that pipx will be in your path.

## Optional but useful addons

1. install metrics
   `minikube addons enable metrics-server`
   then you can use `minikube dashboard`
1. install k9s
   `brew install derailed/k9s/k9s`

## Install CI Butler (pre-release) from OSDU gitlab built packages

To install CI Butler we recommend using pipx:
``` bash title="Install CI Butler"
pipx install cibutler --index-url https://community.opengroup.org/api/v4/projects/1558/packages/pypi/simple --pip-args="--extra-index-url=https://community.opengroup.org/api/v4/projects/148/packages/pypi/simple"
```

## CI Butler Check Prerequisites for Deploying CImpl locally

``` bash title="Check Prerequisites"
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

For more details on what happens in the CImpl install process see [install process](install_process.md).

## Confirm things are working

### Tunnel

Once you have CImpl deployed locally (with our without data) in minikube you'll need to run tunnel to be able to redirect your network to get to kubernetes pods running in the minikube docker container. Tunnel does require administrative privileges (via sudo).

To do that, run one of the following:

``` bash title="Tunnel"
cibutler tunnel
```
Alternatively you can run `minikube tunnel`.
You are now ready to connect to OSDU and other services like keycloak.

### Get access/refresh tokens

Get an access token:
``` bash title="cibutler to get an Access Token"
cibutler token
```

Get a refresh token:
``` bash title="cibutler to get a Refresh Token"
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

``` bash title="cibutler to check status of OSDU services"
cibutler status
```

### Get Client Secret

One of the following:

``` bash title="cibutler to check get client-secret"
cibutler client-secret
```

alternatively you can run kubectl directly:

``` bash title="kubectl command"
kubectl get secret keycloak-bootstrap-secret -o jsonpath="{.data.KEYCLOAK_OSDU_ADMIN_SECRET}" | base64 --decode
```

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

``` bash title="kubectl command"
kubectl get po | grep bootstrap-data
```

Or use K9s to check on the pod status
When pods in Ready column will look like "1/1" the process is finished.

## Delete / Uninstall

### To completely remove CImpl run one of the following

- `cibutler delete`
- `minikube delete`

### To completely remove cibutler

`pipx uninstall cibutler`

## Upgrading

Run the following command to check your version and get instructions how to upgrade

``` bash title="version command"
cibutler version
``` 