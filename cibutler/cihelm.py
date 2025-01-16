import subprocess

from rich.console import Console
import typer

console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)


def helm_uninstall(name="osdu-cimpl"):
    console.print(f"Uninstalling {name}...")
    output = subprocess.Popen(
        ["helm", "uninstall", name], stdout=subprocess.PIPE
    ).communicate()[0]
    return output.decode("ascii").strip()


def helm_list():
    """
    Return list from helm
    """
    try:
        output = subprocess.run(["helm", "list", "-a", "-A"], capture_output=True)
    except subprocess.CalledProcessError as err:
        return str(err)
    else:
        return output.stdout.decode("ascii").strip()


@cli.command(rich_help_panel="Troubleshooting Commands", name="helm-list")
def helm_list_command():
    """
    Show all releases in all namespaces
    """
    console.print(helm_list())


def helm_query(name):
    return name in helm_list()


if __name__ == "__main__":
    cli()
