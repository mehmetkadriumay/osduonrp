# Install OSDU :material-download:

## CI Butler Check Prerequisites

``` bash title="Check Prerequisites"
cibutler check
```

If no issues are reported you should have a successful deployment of OSDU CImpl

## Install CImpl

By default CIButler will prompt for deployment target and version.

If you select Minikube, it will configure and start Minikube and use that as the target for CImpl.
CI Butler will attempt to make educated guesses on how much RAM and CPU to give Minikube/CImpl based upon settings in Docker and the hardware that you have.

If you select anything other than Minikube you need to deploy that and have kubernetes properly configured before running `cibutler install`

```
cibutler install
```

If you want to ignore these recommendations for minikube (potentially useful if you have less CPU or RAM than required - for example Apple Silicon with 24GB RAM):

```
cibutler install --max-cpu --max-memory
```

### Select Deployment Target

Minikube is the original and most thoroughly tested deployment target for CI Butler, particularly within automated pipelines. However, it requires a tunnel for access, which may limit its ease of use in remote environments or when supporting multiple users.

```
[?] Where do you plan to install?:
 > Minikube running inside docker (Supported: All releases)
   Kubernetes (Kubeadm) running in docker-desktop - single node cluster (Partially Supported)
   MicroK8s on this device (Supported: 0.27, Partial 0.28)
   Kubernetes (Kind) running in docker-desktop (Unsupported)
   K3s (Containerd) on this device (Unsupported)
   K3d on this device (Supported: 0.27)
   Other Kubernetes Cluster (Unsupported)
```

### Select Version

Select the version of OSDU to install (specifying both the Helm chart version and its source).
Please note that the CI Butler does not currently maintain its own Helm charts; instead, it installs charts that are either verified to work or available for testing.

```
Note: * Some issues reported for some kubernetes distributions
[?] What Helm Version (typically also the OSDU Version)?:
 > 0.27.0-local           (M24 Oct 2024 x86)       Tested and Working  GC BareMetal
   0.27.0-local           (M24 Oct 2024 arm only)  Tested and Working  GC BareMetal
   0.27.0-local-test      (M24 Oct 2024 x86)       Untested            GC BareMetal
   0.27.2                 (M24 Nov 2024 x86 only)  Untested            GC BareMetal
   0.27.3                 (M24 Jan 2025 x86 only)  Untested            GC BareMetal
   0.28.0-local-c18982c9a (M25 April 2025 multi)   Tested *            GC BareMetal
```

### Select Data Load Option

Next you'll select which data load option. Please note the estimated times are just average time.
If you have a fast system with a fast internet connection it may take less time.
```
dd-reference - upload only part of reference data (10000 records). Estimated time: ~10min,

partial-dd-reference - upload all for reference data. Estimated time: ~30min,
tno-volve-reference - upload all TNO data. Estimated time: ~1h 15min,
all - upload reference and workproduct data Estimated time: ~4h,

Select which data load option:

[?] What data would you like to load?:
 > dd-reference
   partial-dd-reference
   tno-volve-reference
   all
   skip
```

### Automated installs

If you want to have a install data loading and not have to select it later:

``` bash title="Install with data loading in one step"
cibutler install --data-load-flag=tno-volve-reference
```

If you want to have a more automated install without data loading:

``` bash title="Install without data loading in one step"
cibutler install --data-load-flag=skip --force
```

For more details on what happens in the CImpl install process see [install process](install_process.md).

You can also add a `--quiet` less output. See `cibutler install --help` for additional options.
For full options on install see [Command Reference](./commands_reference.md).

## Confirm things are working

### Minikube Tunnel

!!! info "Tunnel"

    Tunnelling is only required when you are deploying on **Minikube**.

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
cibutler diag client-secret
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

If you selected to load data `cibutler install` will not exit until data loading is completed, or it detects errors. However you can also check that data loading finished by running:

``` bash title="kubectl command"
kubectl get po | grep bootstrap-data
```

Or use K9s to check on the pod status
When pods in Ready column will look like "1/1" the process is finished.

## Delete / Uninstall

### To completely remove CImpl OSDU Deployment run 

- `cibutler delete`

!!! question "Additional Documentation is Available"
    **CI Butler has great built-in help**:

     - `cibutler --help` for overall help
     - `cibutler command --help` for help on a individual command

    There is also a command feference on all the commands and options:

    - See [Command Reference](./commands_reference.md).