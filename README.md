# CI Butler
CI (Community Implementation) Butler is an easy to use tool for installing OSDU locally.

In short, CIButler is a tool for development, automation, testing and interacting with OSDU directly. It was built to make installing Community Implementation of OSDU easier and faster with OSDU. Some features could also potentially be used for cloud based deployments.

CIbutler started as a fork of [install-cimpl.sh](https://gitlab.opengroup.org/osdu/pmc/community-implementation/-/blob/main/install-cimpl.sh) and incorporating features & learnings from [AdminCLI](https://osdu.pages.opengroup.org/ui/admincli/) and [simple_osdu_docker_desktop](https://community.opengroup.org/osdu/platform/deployment-and-operations/infra-gcp-provisioning/-/tree/master/examples/simple_osdu_docker_desktop). CI Butler also is built with [OSDU Python SDK](https://community.opengroup.org/osdu/platform/system/sdks/common-python-sdk)

The CI Butler is known to work best on Mac, but should also work on Windows and Linux.
CI Butler is in **very early alpha stage**.

# Requirements
- Mac OS, Windows or Linux
- 150GB of free disk space
- Min. 32GB of RAM. Limited success and testing with Mac with 24GB of RAM. Hope to test more in the future.
- 6 logical processors. Limited success with 4 logical processors

# Installation Instructions

## Install configure prerequisites
1. Install docker desktop
1. Install helm
1. Install minikube
1. Increase RAM in docker desktop to 24+ GB and restart docker
1. Install uv (or pipx)

## Optional
1. install metrics
   `minikube addons enable metrics-server`
   then you can use `minikube dashboard`
1. install k9s
   `brew install derailed/k9s/k9s`

## CIButler Support
Currently CI Butler only supports minikube with Docker.
However in future support could be added for: QEMU, Hyperkit, Hyper-V, KVM, Parallels, Podman, VirtualBox, or VMware Fusion/Workstation


# Install cibutler
## Install from source
If you have cibutler already checked out
`uv run cibutler`

## Install from gitlab built packages


## Pre CI Impl Preflight check
`cibutler check`

## Install CImpl
CI Butler will attempt to make educated guesses on how much RAM and CPU to give OSDU based upon settings in Docker and the hardware that you have.

`cibutler install`

If you want to ignore these recommendations (especially useful if you have less CPU or RAM than required)

`cibutler install --max-cpu --max-memory`

If you want to have a install data loading and not have to select it later
`cibutler install --data-load-flag=tno-volve-reference`

If you want to have a fully automated install without data loading 
`cibutler install --data-load-flag=skip --quiet`

# Delete
One of the following:
- `minikube delete`
- `cibutler delete`

# Get access/refresh tokens
`cibutler token`
`cibutler refresh-token`

```
curl --location 'http://keycloak.localhost/realms/osdu/protocol/openid-connect/token' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode 'grant_type=client_credentials' \
--data-urlencode 'client_id=osdu-admin' \
--data-urlencode 'client_secret=GBZcYxWiqe1at939' \
--data-urlencode 'scope=email openid profile'
```

# fetch the WellboreTrajectory 1.1.0 schema:

```
curl --location 'http://osdu.localhost/api/schema-service/v1/schema/osdu:wks:work-product-component--WellboreTrajectory:1.1.0' \
--header 'Content-Type: application/json' \
--header 'data-partition-id: osdu' \
--header 'Authorization: Bearer <access_token_here>'
```

# Core Smoke Test Collection and the "client_credentials" grant_type and HOSTNAME=http://osdu.localhost

# To get your client_secret execute command:
- `cibutler client-secret`
- `kubectl get secret keycloak-bootstrap-secret -o jsonpath="{.data.KEYCLOAK_OSDU_ADMIN_SECRET}" | base64 --decode`

# Data loading
To check that data loading finished use command:
`kubectl get po | grep bootstrap-data`

Or use K9s to check on the pod status
When pods in Ready column will look like "1/1" the process is finished.