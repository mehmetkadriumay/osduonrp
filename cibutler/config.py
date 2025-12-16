import os
import typer
import inquirer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from typing_extensions import Annotated
from rich.panel import Panel
import rich.box
import ruamel.yaml
import cibutler.downloader as downloader
import cibutler.utils as utils

# Map of friendly service names to the helm value flags that enable/disable them.
SERVICE_FLAG_MAP = {
    # Infra building blocks
    "Airflow": [
        "airflow.enabled",
        "airflow.airflow-infra-bootstrap.enabled",
    ],
    "Elastic": [
        "elasticsearch.enabled",
        "elasticsearch.elastic-infra-bootstrap.enabled",
        "elastic-bootstrap.enabled",
    ],
    "Keycloak": [
        "keycloak.enabled",
        "keycloak.keycloak-infra-bootstrap.enabled",
    ],
    "Minio": [
        "minio.enabled",
        "minio.minio-infra-bootstrap.enabled",
    ],
    "PostgreSQL": [
        "postgresql.enabled",
        "postgresql.postgres-infra-bootstrap.enabled",
    ],
    "Common-Infra": [
        "common-infra-bootstrap.enabled",
    ],
    "RabbitMQ-Bootstrap": [
        "cimpl-bootstrap-rabbitmq.enabled",
    ],
    # OSDU services
    "Crs-catalog": ["core-plus-crs-catalog-deploy.enabled"],
    "Crs-conversion": ["core-plus-crs-conversion-deploy.enabled"],
    "Dataset": ["core-plus-dataset-deploy.enabled"],
    "Entitlements": ["core-plus-entitlements-deploy.enabled"],
    "File": ["core-plus-file-deploy.enabled"],
    "Indexer": ["core-plus-indexer-deploy.enabled"],
    "Legal": ["core-plus-legal-deploy.enabled"],
    "Notification": ["core-plus-notification-deploy.enabled"],
    "Partition": ["core-plus-partition-deploy.enabled"],
    "Policy": ["core-plus-policy-deploy.enabled"],
    "Register": ["core-plus-register-deploy.enabled"],
    "Schema": ["core-plus-schema-deploy.enabled"],
    "Search": ["core-plus-search-deploy.enabled"],
    "Storage": ["core-plus-storage-deploy.enabled"],
    "Unit": ["core-plus-unit-deploy.enabled"],
    "Wellbore": ["core-plus-wellbore-deploy.enabled"],
    "Wellbore-Worker": ["core-plus-wellbore-worker-deploy.enabled"],
    "Workflow": ["core-plus-workflow-deploy.enabled"],
    "Secret": ["core-plus-secret-deploy.enabled"],
}


console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich",
    help="CI Butler - an OSDU Community Implementation utility",
    no_args_is_help=True,
)

diag_cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)


configurable_services = list(SERVICE_FLAG_MAP.keys())


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands")
def config(
    defaults: Annotated[
        bool,
        typer.Option("--default", help="Show only default values for configuration"),
    ] = False,
):
    """
    Get the configuration for the CImpl installation.
    """
    rabbitmq_password = utils.random_password()
    redis_password = utils.random_password()
    default_choices = configurable_services.copy()
    locked_choices = []

    if defaults:
        answers = {
            "rabbitmq_password": rabbitmq_password,
            "redis_password": redis_password,
            "osdu_services": default_choices,
        }
        return answers

    output = """    [yellow]:warning: This is an alpha feature and is not yet fully supported.[/yellow]

    A limited number of services can be optionally configured, while
    others are locked.  Adjusting the configuration will change the
    installation and could result in a failed deployment.  Results may
    vary depending on the services selected and which OSDU version/Helm
    Version selected.

    Note: Not all OSDU Versions and their associated Helm Charts support
    customization of the OSDU Services.  The default is to use the
    services that are enabled by default in the Helm Chart unless there
    is a known issue or lack of testing.

    [green][bold]Taking the defaults is recommended for most users.[/bold][/green]

    However feel free to experiment, but be aware that it may not work as
    expected.  In future releases, this will be more robust and tested.

    Passwords here are randomly generated, but can be customized if desired.
    
    This feature is provided as a convenience to the community and
    is not yet fully supported.  It is intended to allow users to
    customize their OSDU installation with minimal effort, but it is
    not guaranteed to work in all cases.  If you encounter issues, please
    report them to the OSDU community via the [bold]#cap-cibutler[/bold]
    channel in the OSDU Slack workspace.
    """
    console.print(
        Panel(
            "\n" + output,
            box=rich.box.SQUARE,
            expand=True,
            title="[cyan]Customize OSDU[/cyan]",
        )
    )

    questions = [
        inquirer.Text(
            "rabbitmq_password", message="RabbitMQ Password", default=rabbitmq_password
        ),
        inquirer.Text(
            "redis_password", message="Redis Password", default=redis_password
        ),
        inquirer.Checkbox(
            "osdu_services",
            message="Enable which OSDU Services?",
            choices=sorted(configurable_services),
            default=default_choices,
            locked=locked_choices,
        ),
    ]
    answers = inquirer.prompt(questions)
    return answers


def prompt(ask, password=True, default=None, length=8):
    while True:
        value = Prompt.ask(ask, default=default, password=password)
        if len(value) >= length:
            break
        console.print("[prompt.invalid]password too short")
    return value


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands")
def configure(
    default_random_password: bool = typer.Option(
        True, "--random", help="Use random passwords"
    ),
    interactive: bool = typer.Option(True, "--prompt", help="Prompt for values"),
):
    """Configure CImpl custom values file  :wrench:"""
    filename = "values.yaml"
    # url = "https://community.opengroup.org/osdu/platform/deployment-and-operations/infra-gcp-provisioning/-/raw/master/examples/simple_osdu_docker_desktop/custom-values.yaml"
    url = "https://community.opengroup.org/osdu/platform/deployment-and-operations/base-containers-cimpl/osdu-cimpl-stack/-/raw/main/helm/values.yaml"

    if os.path.isfile(filename):
        console.print(f"{filename} exists")
    else:
        downloader.download([url], "./")
    data = custom_values(filename=filename)
    if not data:
        error_console.print(f"Unable to read {filename}")
        raise typer.Exit(1)

    try:
        if default_random_password:
            minio_password = utils.random_password()
            keycloak_admin_password = utils.random_password()
            postgresql_password = utils.random_password()
            airflow_externaldb_password = utils.random_password()
            airflow_password = utils.random_password()
            elasticsearch_password = utils.random_password()
            rabbitmq_password = utils.random_password()
        else:
            minio_password = data["minio"]["auth"]["rootPassword"]
            # keycloak_admin_password = data["keycloak"]["auth"]["adminPassword"]
            postgresql_password = data["postgresql"]["global"]["postgresql"]["auth"][
                "postgresPassword"
            ]
            airflow_externaldb_password = data["airflow"]["externalDatabase"][
                "password"
            ]
            airflow_password = data["airflow"]["auth"]["password"]
            elasticsearch_password = data["elasticsearch"]["security"][
                "elasticPassword"
            ]
            # rabbitmq_password = data["rabbitmq"]["auth"]["password"]
        domain = data["common-infra-bootstrap"]["global"]["domain"]
        # limits_enabled = str(data["global"]["limitsEnabled"]).lower()
    except KeyError as e:
        error_console.print(f"Key {e} not found in {filename}.")
        raise typer.Exit(1)

    useInternalServerUrl = "true"
    hide = True
    domain = Prompt.ask("Domain", default=domain)

    # limits_enabled = Prompt.ask(
    #    "limitsEnabled", choices=["true", "false"], default=limits_enabled
    # )
    # keycloak_admin_password = prompt(
    #    "Keycloak Password", password=hide, default=keycloak_admin_password
    # )
    if interactive:
        minio_password = prompt("Minio Password", password=hide, default=minio_password)
        postgresql_password = prompt(
            "Postgresql Password", password=hide, default=postgresql_password
        )
        airflow_externaldb_password = prompt(
            "Airflow ExternalDB Password",
            password=hide,
            default=airflow_externaldb_password,
        )
        airflow_password = prompt(
            "Airflow Password", password=hide, default=airflow_password
        )
        elasticsearch_password = prompt(
            "ElasticSearch Password", password=hide, default=elasticsearch_password
        )
        rabbitmq_password = prompt(
            "RabbitMQ Password", password=hide, default=rabbitmq_password
        )
        use_internal_server_url = Prompt.ask(
            "useInternalServerUrl",
            choices=["true", "false"],
            default=useInternalServerUrl,
        )

    try:
        # Airflow
        data["airflow"]["externalDatabase"]["password"] = airflow_externaldb_password
        data["airflow"]["auth"]["password"] = airflow_password
        data["airflow"]["airflow-infra-bootstrap"]["domain"] = domain
        data["common-infra-bootstrap"]["global"]["domain"] = domain
        data["common-infra-bootstrap"]["airflow"]["auth"]["password"] = airflow_password
        data["common-infra-bootstrap"]["airflow"]["externalDatabase"]["password"] = (
            airflow_password
        )

        # Elasticseach
        data["elasticsearch"]["security"]["elasticPassword"] = elasticsearch_password
        data["elasticsearch"]["elastic-infra-bootstrap"]["global"]["domain"] = domain
        data["elasticsearch"]["elastic-infra-bootstrap"]["elastic_bootstrap"][
            "elasticPassword"
        ] = elasticsearch_password

        # Minio
        # data["global"]["limitsEnabled"] = bool(limits_enabled)
        data["minio"]["auth"]["rootPassword"] = minio_password
        data["minio"]["minio-infra-bootstrap"]["global"]["domain"] = domain
        data["minio"]["minio-infra-bootstrap"]["minio"]["auth"]["rootPassword"] = (
            minio_password
        )
        # data["minio"]["useInternalServerUrl"] = bool(use_internal_server_url)
        # data["keycloak"]["auth"]["adminPassword"] = keycloak_admin_password

        # postgresql
        data["postgresql"]["global"]["postgresql"]["auth"]["postgresPassword"] = (
            postgresql_password
        )
        data["postgresql"]["postgres-infra-bootstrap"]["global"]["domain"] = domain
        data["postgresql"]["postgres-infra-bootstrap"]["postgresql"]["global"][
            "postgresql"
        ]["auth"]["postgresPassword"] = postgresql_password

        # common-infra-bootstrap
        data["common-infra-bootstrap"]["global"]["domain"] = domain
        data["common-infra-bootstrap"]["airflow"]["auth"]["password"] = airflow_password
        data["common-infra-bootstrap"]["airflow"]["externalDatabase"]["password"] = (
            airflow_externaldb_password
        )

        # cimpl-bootstrap-rabbitmq
        data["cimpl-bootstrap-rabbitmq"]["rabbitmq"]["auth"]["password"] = (
            rabbitmq_password
        )

        # OSDU Services values
        data["core-plus-crs-catalog-deploy"]["global"]["domain"] = domain
        data["core-plus-crs-conversion-deploy"]["global"]["domain"] = domain
        data["core-plus-dataset-deploy"]["global"]["domain"] = domain
        data["core-plus-entitlements-deploy"]["global"]["domain"] = domain
        data["core-plus-file-deploy"]["global"]["domain"] = domain
        data["core-plus-indexer-deploy"]["global"]["domain"] = domain
        data["core-plus-legal-deploy"]["global"]["domain"] = domain
        data["core-plus-notification-deploy"]["global"]["domain"] = domain
        data["core-plus-partition-deploy"]["global"]["domain"] = domain
        data["core-plus-policy-deploy"]["global"]["domain"] = domain
        data["core-plus-register-deploy"]["global"]["domain"] = domain
        data["core-plus-schema-deploy"]["global"]["domain"] = domain
        data["core-plus-search-deploy"]["global"]["domain"] = domain
        data["core-plus-storage-deploy"]["global"]["domain"] = domain
        data["core-plus-unit-deploy"]["global"]["domain"] = domain
        data["core-plus-wellbore-deploy"]["global"]["domain"] = domain
        data["core-plus-wellbore-worker-deploy"]["global"]["domain"] = domain
        data["core-plus-workflow-deploy"]["global"]["domain"] = domain
        data["core-plus-secret-deploy"]["global"]["domain"] = domain

    except KeyError as e:
        error_console.print(f"Key {e} not found in processing {filename}.")
        raise typer.Exit(1)

    if Confirm.ask("Save?", default=True):
        with open(filename, "w") as file:
            yaml = ruamel.yaml.YAML()
            yaml.dump(data, file)
            console.print(f"Updated: {filename}")

    # if Confirm.ask("Install?", default=True):
    #    output = helm_install()
    #    console.print(output)


def custom_values(filename="custom-values.yaml"):
    try:
        with open(filename, "r") as config:
            # try:
            # data = yaml.safe_load(config)
            yaml = ruamel.yaml.YAML()
            data = yaml.load(config)
            # except yaml.YAMLError as err:
            # except yaml.YAMLError as err:
            #    print(err)
            # console.print(data)
            # yaml.dump(data, sys.stdout)
            return data
    except FileNotFoundError:
        error_console.print(f"File {filename} Not found")
        return None


if __name__ == "__main__":
    diag_cli()
