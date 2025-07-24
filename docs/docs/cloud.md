# Cloud testing

Google generously provided temporary compute resources to support testing of CI Butler. To leverage this, I implemented automation to create a VM in Google Cloud and install CI Butler. Support for GKE deployment is planned for a future release.

## Setup 

Install and configure [gcloud cli](https://cloud.google.com/sdk/docs/install).

While optional I highly recommend creating a `.env.cibutler` file in your home directory, but you can always provide those details on command-line

```
HOST = 
PROJECT = 
INSTANCE = 
ZONE = 
```

## Testing Steps
1. `cibutler diag gcloud-instance-create` to create a VM on gcloud
1. `cibutler diag gcloud-config-ssh` to configure ssh
1. ssh to instance to accept keys (command shown above)
1. `cibutler diag ssh` to test connection
1. `cibutler diag cloud_install_ubuntu_microk8s` to install cibutler on remote Ubuntu host running over ssh
1. ssh to instance and start install
    * `cibutler install -k --max-memory --max-cpu -d tno-volve-reference` 

## Related Testing Commands

- `cibutler diag gcloud-instance-start`
- `cibutler diag gcloud-instance-stop`
- `cibutler diag gcloud-instance-delete`