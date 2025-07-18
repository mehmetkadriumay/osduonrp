import typer
from rich.console import Console
import inquirer
import logging
from cibutler._version import __version__ as cibutler_version

logger = logging.getLogger(__name__)

import logging
from rich.console import Console

console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

diag_cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)


@diag_cli.command(rich_help_panel="Diagnostic Commands", hidden=True)
def select_version(defaults: bool = False):
    if defaults:
        return (
            "0.28.0-local-c18982c9a",
            "oci://us-central1-docker.pkg.dev/or2-msq-gnrg-osdu-mp-t1iylu/cimpl/helm/osdu-cimpl",
        )

    versions = {
        "0.27.0-local           (M24 Oct 2024 x86)       Tested and Working  GC BareMetal": "oci://us-central1-docker.pkg.dev/or2-msq-gnrg-osdu-mp-t1iylu/cimpl/helm/osdu-cimpl",
        "0.27.0-local           (M24 Oct 2024 arm only)  Tested and Working  GC BareMetal": "oci://us-central1-docker.pkg.dev/or2-msq-gnrg-osdu-mp-t1iylu/cimpl/helm/osdu-cimpl-arm",
        "0.27.0-local-test      (M24 Oct 2024 x86)                           GC BareMetal": "oci://us-central1-docker.pkg.dev/or2-msq-gnrg-osdu-mp-t1iylu/cimpl/helm/osdu-cimpl",
        "0.27.2                 (M24 Nov 2024 x86 only)                      GC BareMetal": "oci://us-central1-docker.pkg.dev/or2-msq-gnrg-osdu-mp-t1iylu/cimpl/helm/osdu-cimpl",
        "0.27.3                 (M24 Jan 2025 x86 only)                      GC BareMetal": "oci://us-central1-docker.pkg.dev/or2-msq-gnrg-osdu-mp-t1iylu/cimpl/helm/osdu-cimpl",
        "0.28.0-local-c18982c9a (M25 April 2025 multi)   Tested and Working  GC BareMetal": "oci://us-central1-docker.pkg.dev/or2-msq-gnrg-osdu-mp-t1iylu/cimpl/helm/osdu-cimpl",
    }

    options = []
    for version, source in versions.items():
        options.append(f"{version}")

    console.print(f"Current deployments known to CI Butler {cibutler_version}:")
    questions = [
        inquirer.List(
            "helm_version",
            message="What Helm Version (typically also the OSDU Version)?",
            default=options[-1],
            choices=options,
        ),
    ]
    answers = inquirer.prompt(questions)
    selected_option = str(answers["helm_version"]).split(" ")[0]

    console.print(f"You selected: {selected_option}")
    logger.info(
        f"{versions[answers['helm_version']]} and version {selected_option} selected for installation"
    )

    # return the selected version and its corresponding source
    return selected_option, versions[answers["helm_version"]]


if __name__ == "__main__":
    diag_cli()
