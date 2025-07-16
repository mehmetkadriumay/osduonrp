import typer
from pick import pick
from rich.console import Console
from typing_extensions import Annotated
import inquirer
import logging

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
def select_version():
    versions = {
       "0.27.0-local           (Oct 2024 x86)       Tested and Working" :
         "oci://us-central1-docker.pkg.dev/or2-msq-gnrg-osdu-mp-t1iylu/cimpl/helm/osdu-cimpl",
       "0.27.0-local           (Oct 2024 arm only)  Tested and Working": 
         "oci://us-central1-docker.pkg.dev/or2-msq-gnrg-osdu-mp-t1iylu/cimpl/helm/osdu-cimpl-arm",
       "0.27.2                 (Nov 2024 x86 only)": 
        "oci://us-central1-docker.pkg.dev/or2-msq-gnrg-osdu-mp-t1iylu/cimpl/helm/osdu-cimpl",
       "0.27.3                 (Jan 2025 x86 only)":
        "oci://us-central1-docker.pkg.dev/or2-msq-gnrg-osdu-mp-t1iylu/cimpl/helm/osdu-cimpl",
       "0.28.0-local-c18982c9a (April 2025 multi)":
        "oci://us-central1-docker.pkg.dev/or2-msq-gnrg-osdu-mp-t1iylu/cimpl/helm/osdu-cimpl",
    }

    options = []
    for version, source in versions.items():
        options.append(f"{version}")

    questions = [
        inquirer.List(
            "helm_version",
            message="What Helm Version (typically also the OSDU Version)?",
            choices=options,
        ),
    ]
    answers = inquirer.prompt(questions)
    selected_option = str(answers["helm_version"]).split(" ")[0]

    console.print(f"You selected: {selected_option}")
    logger.info(f"{versions[answers['helm_version']]} and version {selected_option} selected for installation")

    # return the selected version and its corresponding source
    return selected_option, versions[answers["helm_version"]]


if __name__ == "__main__":
    diag_cli()