# OSDU CI Butler

CI Butler (or CIButler) is a user-friendly command-line interface (CLI) tool designed to simplify the local installation of OSDU. It serves as a convenient utility for development, automation, testing, and direct interaction with the OSDU platform.

CI Butler was developed by Shane Hutchins to streamline and accelerate the setup of the Community Implementation of OSDU, aiming to make the platform more accessible and efficient for contributors and developers.


CI Butler is supported on macOS, Windows, and Linux. While it is known to perform best on macOS, it should also function reliably on both Windows and Linux systems.k

!!! warning "Experimental"

    CI Butler is currently under development and should be considered experimental. Please report any issues you encounter.

!!! warning "Production Use"

    Please note that CIButler is not intended for production environments and does not meet the security requirements necessary for production use.

CIButler was inspired by the great work by the Google Team (namely [install-cimpl.sh](https://gitlab.opengroup.org/osdu/pmc/community-implementation/-/blob/main/install-cimpl.sh),
[simple_osdu_docker_desktop](https://community.opengroup.org/osdu/platform/deployment-and-operations/infra-gcp-provisioning/-/tree/master/examples/simple_osdu_docker_desktop))
and incorporating features & learnings from [AdminCLI](https://osdu.pages.opengroup.org/ui/admincli/). 
CI Butler is also built with [OSDU Python SDK osdu-api](https://community.opengroup.org/osdu/platform/system/sdks/common-python-sdk). 

!!! example "Work in Progress"

    Note: CI Butler is not yet using the official Community Implementation Helm charts and container images. Integration with these official resources is planned and will be adopted once they reach a stable release.

    In the meantime, CI Butler defaults to using the M24 and M25 Helm charts and container images provided by the Google team (with thanks to Google for their contributions).

    The versions and paths used during installation are fully configurable and can be easily overridden through command-line options.

    As the community continues to make excellent progress, we anticipate switching to the stable, community-provided charts and images in the near future.

!!! tip "Automation and Testing"

    CI Butler also includes built-in support for managing users and client IDs in [Keycloak](https://www.keycloak.org/), as well as assigning users to OSDU groups.

    This functionality is especially useful when redeploying your OSDU environment for testing purposes or as part of an automated pipeline.


!!! question "Additional Documentation"
    **CI Butler includes comprehensive built-in help, making it easy to explore available commands and options directly from the command line**:

     - `cibutler --help` for overall help
     - `cibutler command --help` for help on a individual command

    In addition to the built-in help, there is also a command reference guide available that provides detailed documentation on all commands, flags, and usage examples:

    - See [Command Reference](./commands_reference.md).

For details on this project see [project details](./project.md).

Last updated on {{ git_revision_date }}