# OSDU CI Butler

The CI Butler (or CIButler) is an easy to use CLI for installing OSDU locally.  In short, CIButler is a tool for development, automation, testing and interacting with OSDU directly. It was built to make installing Community Implementation of OSDU easier and faster with OSDU.
CIButler was not designed to support production needs.

The CIButler is supported on Mac, Windows and Linux.  It is known to work best on Mac, but should also work on Windows and Linux.


CIButler was inspired by the great work by the Google Team (namely [install-cimpl.sh](https://gitlab.opengroup.org/osdu/pmc/community-implementation/-/blob/main/install-cimpl.sh),
[simple_osdu_docker_desktop](https://community.opengroup.org/osdu/platform/deployment-and-operations/infra-gcp-provisioning/-/tree/master/examples/simple_osdu_docker_desktop))
and incorporating features & learnings from [AdminCLI](https://osdu.pages.opengroup.org/ui/admincli/) &
CI Butler also is built with [OSDU Python SDK](https://community.opengroup.org/osdu/platform/system/sdks/common-python-sdk). 

!!! warning "Experimental"

    CI Butler is in development and should be considered experimental. Please report any issues.

!!! example "CI Butler is Not Yet Using Official Community Implementation Helm Charts and Images Yet"
    CI Butler is by default temporarily using the M24 helm charts and container images built by Google (thank you google) as demonstrated during the face to face meeting in Houston 2024 until the official CI helm charts and container images are available.
    
    These versions and paths can however be overridden on the command-line.
    When stable Community provided images are available, CI Butler will be updated to use these by default.

!!! tip "Automation and Testing"
    CI Butler also have built-in support for managing users and client ids in keycloak and adding users to groups OSDU.

    This can be especially useful to when you need to redeploy your OSDU environment or test as part of a pipeline.


!!! question "Additional Documentation"
    **CI Butler has great built-in help**:

     - `cibutler --help` for overall help
     - `cibutler command --help` for help on a individual command

    There is also a command feference on all the commands and options:

    - See [Command Reference](./commands_reference.md).

For details on this project see [project details](./project.md).

Last updated on {{ git_revision_date }}