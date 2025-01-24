# OSDU CI Butler

The CI Butler (or CIButler) is an easy to use CLI for installing OSDU locally.  In short, CIButler is a tool for development, automation, testing and interacting with OSDU directly. It was built to make installing Community Implementation of OSDU easier and faster with OSDU.
CIButler was not designed to support production needs.

The CIButler is supported on Mac, Windows and Linux.  It is known to work best on Mac, but should also work on Windows and Linux.


CIButler was inspired by [install-cimpl.sh](https://gitlab.opengroup.org/osdu/pmc/community-implementation/-/blob/main/install-cimpl.sh) and incorporating features & learnings from [AdminCLI](https://osdu.pages.opengroup.org/ui/admincli/) & [simple_osdu_docker_desktop](https://community.opengroup.org/osdu/platform/deployment-and-operations/infra-gcp-provisioning/-/tree/master/examples/simple_osdu_docker_desktop). CI Butler also is built with [OSDU Python SDK](https://community.opengroup.org/osdu/platform/system/sdks/common-python-sdk).


CI Butler also have built-in support for managing users and client ids in keycloak and adding users to groups OSDU.
This can be especially useful to when you need to redeploy your OSDU environment or test as part of a pipeline.

!!! warning "Experimental"

    CI Butler is in development and should be considered experimental. Please report any issues.

!!! info "Additional Documentation"
    **CI Butler has built-in help**:

     - `cibutler --help` for overall help
     - `cibutler command --help` for help on a individual command

    There is also a command feference on all the commands and options:

    - See [Command Reference](./commands_reference.md).

For details on this project see [project details](./project.md).

Last updated on {{ git_revision_date }}