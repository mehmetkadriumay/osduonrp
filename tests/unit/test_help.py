import sys
import os
import pytest
from typer.testing import CliRunner
from cibutler.main import cli

runner = CliRunner()


@pytest.mark.skipif(sys.version_info < (3, 11), reason="requires python3.11 or later")
# Test all the helps
def test_main_help():
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0


@pytest.mark.parametrize(
    "test_input",
    [
        ("version"),
    ],
)
def test_utility_commands_help(test_input):
    result = runner.invoke(cli, [test_input, "--help"])
    assert result.exit_code == 0, f"exit status, stdout: {result.stdout}"


@pytest.mark.parametrize(
    "test_input",
    [
        ("list-pods"),
        ("services"),
        ("ready"),
        ("ingress"),
        ("config-minikube"),
        ("update-services"),
        ("notebook"),
        ("check-running"),
        ("client-secret"),
        ("post-message"),
        ("helm-list"),
        ("docker-info"),
        ("upload-data"),
        ("cpu"),
    ],
)
def test_diag_commands_help(test_input):
    result = runner.invoke(cli, ["diag", test_input, "--help"])
    assert result.exit_code == 0, f"exit status, stdout: {result.stdout}"


# Help for Policy Developer Utils/Commands
@pytest.mark.parametrize(
    "test_input",
    [("use-context"), ("current-context")],
)
def test_k8s_help(test_input):
    result = runner.invoke(cli, [test_input, "--help"])
    assert result.exit_code == 0, f"exit status, stdout: {result.stdout}"


# Help for Utils/Commands
@pytest.mark.parametrize(
    "test_input",
    [
        ("token"),
        ("list-clients"),
        ("add-client"),
        ("list-users"),
        ("client-id"),
        ("add-users"),
        ("add-user"),
        ("set-password"),
        ("delete-user"),
    ],
)
def test_keycloak_commands_help(test_input):
    result = runner.invoke(cli, [test_input, "--help"])
    assert result.exit_code == 0, f"exit status, stdout: {result.stdout}"


# Help for system
@pytest.mark.parametrize(
    "test_input",
    [
        ("refresh-token"),
        ("legal-tags"),
        ("groups"),
        ("group-members"),
        ("group-add"),
        ("groups-add"),
        ("group-del"),
        ("search"),
        ("record"),
        ("status"),
        ("info"),
        ("envfile"),
    ],
)
def test_osdu_commands_help(test_input):
    result = runner.invoke(cli, [test_input, "--help"])
    assert result.exit_code == 0, f"exit status, stdout: {result.stdout}"
