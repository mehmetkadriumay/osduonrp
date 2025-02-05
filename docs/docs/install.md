# Install :material-download:
## Requirements for using CI Butler and deploying CImpl locally

!!! example "Support"
    Currently CI Butler only supports **minikube with Docker** and deploying on **Kubernetes with Docker-Desktop** (built-in kubernetes).

    - Additionally CIButler only supports a single deployment to a kubernetes cluster.
    - Multiple deployments to different minikubes or separated by namespaces are not supported.
    - Using both CImpl on minikube and CImpl on Kubernetes with Docker Desktop at the same time is not currently supported. However if you manage the istio/ingress it should work.
    - Success has been reported that local install to microk8s on Ubuntu works, however this is officially not supported or tested. You'll likely have to adjust istio/ingress on your own.

    However in future support could be added for:

    - Namespace separation (allowing multiple deployments),
    - Deploying to other small local kubernetes (microk8s, kind, k3s, etc)
    - Other remote kubernetes deployments (even cloud based),
    - Minikube support for more than docker driver (i.e. QEMU, Hyperkit, Hyper-V, KVM, Parallels, Podman, VirtualBox, VMware Fusion/Workstation, etc.)

    If you're interested in one of these please open an [issue](https://community.opengroup.org/osdu/ui/cibutler/-/issues/) to request it.

!!! info "Install Requirements for installing CImpl locally"

    If you're don't intend to install CImpl locally but are using CI Butler as part of a pipeline or automation these requirements can be ignored.

    - Mac OS, Windows or Linux
    - 150GB of free disk space
    - Min. 32GB of RAM. Limited success and testing with Mac with 24GB of RAM. Hope to test more in the future.
    - 6 logical processors. Limited success with 4 logical processors

    CIButler supports MacOS, Windows and Linux, and has been tested most often with:

    - MacOS Sequoia 15.2 and later
    - Windows11 - some users have reported needing [Microsoft C++ build tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) installed.


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

- Currently CI Butler only supports minikube with Docker and deploying to Docker-Desktop's built-in kubernetes.
- Both are easy to use options and use the same basic commands to install, use and delete.
- Using Kubernetes in Docker Desktop sometimes performs a little better since you have one less level of virtualization.

#### Deploy on Minikube
If you intend to deploy CImpl locally using minikube you'll need the following:

1. Install [docker desktop](https://www.docker.com/products/docker-desktop/) :simple-docker:
1. Install [helm](https://helm.sh/docs/intro/install/) :simple-helm:
1. Install [minikube](https://minikube.sigs.k8s.io/docs/start)
1. Install kubectl :simple-kubernetes: if not already included in the above (docker desktop normally includes it). CIButler attempts to be a pure python implementation but uses both APIs and `kubectl` to configure and deploy to kubernetes.
1. Increase RAM in docker desktop to 24+ GB and restart docker
1. Increase CPU limit in docker desktop to 6 or more cores. For the best performance setting it to the number of high performance cores is recommended.
1. Add [Hosts file entries](./install.md#host-entries).
1. Install Python3.11 or later. CIButler has not yet been tested with Python3.14.x
1. Install [pipx](./install.md#how-to-install-pipx) 
1. and then [install CI Butler](./install.md#install-ci-butler-pre-release-from-osdu-gitlab-built-packages) of course :smile:
1. [CI Butler check](./install.md#ci-butler-check-prerequisites)

#### Deploy on Kubernetes with Docker Desktop
If you intend to deploy CImpl locally using kubernetes inside docker-desktop you'll need the following:

1. Install [docker desktop](https://www.docker.com/products/docker-desktop/) :simple-docker:
1. Install [helm](https://helm.sh/docs/intro/install/) :simple-helm:
1. Install kubectl :simple-kubernetes: if not already included in the above (docker desktop normally includes it). CIButler attempts to be a pure python implementation but uses both APIs and `kubectl` to configure and deploy to kubernetes.
1. Increase RAM in docker desktop to 24+ GB and restart docker
1. Increase CPU limit in docker desktop to 6 or more cores. For the best performance setting it to the number of high performance cores is recommended.
1. Add [Hosts file entries](./install.md#host-entries).
1. Install Python3.11 or later. CIButler has not yet been tested with Python3.14.x
1. Install [pipx](./install.md#how-to-install-pipx) 
1. and then [install CI Butler](./install.md#install-ci-butler-pre-release-from-osdu-gitlab-built-packages) of course :smile:
1. [CI Butler check](./install.md#ci-butler-check-prerequisites)

---

### Host Entries :material-dns-outline:

Alternatively if you are deploying CImpl on minikube you can use the [minikube ingress addons](https://minikube.sigs.k8s.io/docs/handbook/addons/ingress-dns/) but my recommendation is to add these entries into `/etc/hosts` or `C:\Windows\System32\drivers\etc\hosts`. These entries are also required for deploying CImpl on Kubernetes with Docker Desktop.
``` title="Host file entries"
127.0.0.1 osdu.localhost osdu.local
127.0.0.1 airflow.localhost airflow.local
127.0.0.1 minio.localhost minio.local
127.0.0.1 keycloak.localhost keycloak.local
```

---

### How to install Pipx :simple-pipx:

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

---

## Optional but useful addons

1. install metrics for minikube
   `minikube addons enable metrics-server`
   then you can use `minikube dashboard`
1. install k9s
   `brew install derailed/k9s/k9s`

## Install CI Butler (pre-release) from OSDU gitlab built packages

To install CI Butler we recommend using pipx:
``` bash title="Install CI Butler"
pipx install cibutler --index-url https://community.opengroup.org/api/v4/projects/1558/packages/pypi/simple --pip-args="--extra-index-url=https://community.opengroup.org/api/v4/projects/148/packages/pypi/simple"
```

## CI Butler Check Prerequisites

This is required if you are Deploying CImpl locally on minikube

``` bash title="Check Prerequisites"
cibutler check
```
This is required if you are Deploying CImpl locally on Kubernetes with Docker Desktop
``` bash title="Check Prerequisites"
cibutler check --all
```

If no issues are reported you should have a successful deployment of OSDU CImpl

## Install CImpl on Minikube

By default CIButler will configure and start Minikube and use that as the target for CImpl.
CI Butler will attempt to make educated guesses on how much RAM and CPU to give Minikube/CImpl based upon settings in Docker and the hardware that you have.

```
cibutler install
```

If you want to ignore these recommendations (especially useful if you have less CPU or RAM than required):

```
cibutler install --max-cpu --max-memory
```

If you want to have a install data loading and not have to select it later:

``` bash title="Install with data loading in one step"
cibutler install --data-load-flag=tno-volve-reference
```

If you want to have a more automated install without data loading:

``` bash title="Install without data loading in one step"
cibutler install --data-load-flag=skip
```
You can also add a `--quiet` less output.

For more details on what happens in the CImpl install process see [install process](install_process.md).
For full options on install see [Command Reference](./commands_reference.md).

## Install CImpl on Kubernetes with Docker Desktop
Make sure you have your kubernetes context to `docker-desktop`.
You can verify this with 
```
cibutler current-context
```

Or change it with
```
cibutler use-context
```

``` bash title="Install on Kubernetes with Docker Desktop"
cibutler install -k
```

## Confirm things are working

### Tunnel

!!! info "Tunnel"

    Tunnelling is only required when you are deploying on minikube.

    Once you have CImpl deployed locally (with our without data) on minikube you'll need to run tunnel to be able to redirect your network to get to kubernetes pods running in the minikube docker container. Tunnel does require administrative privileges (via sudo on Mac and Linux).

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

### To completely remove CImpl run 

- `cibutler delete`

### To completely remove cibutler

`pipx uninstall cibutler`

## Upgrading CI Butler

Run the following command to check your version and get instructions how to upgrade

``` bash title="version command"
cibutler version
``` 

!!! question "Additional Documentation is Available"
    **CI Butler has great built-in help**:

     - `cibutler --help` for overall help
     - `cibutler command --help` for help on a individual command

    There is also a command feference on all the commands and options:

    - See [Command Reference](./commands_reference.md).