import sys
import pytest
from typer.testing import CliRunner
from cibutler.main import cli

runner = CliRunner()


@pytest.mark.skipif(sys.version_info < (3, 11), reason="requires python3.11 or later")
def test_version():
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0


@pytest.mark.skipif(sys.version_info < (3, 11), reason="requires python3.11 or later")
def test_delete():
    result = runner.invoke(cli, ["delete", "--force"])
    assert result.exit_code == 0


@pytest.mark.skipif(sys.version_info < (3, 11), reason="requires python3.11 or later")
def test_check_minikube():
    result = runner.invoke(cli, ["check", "--target", "minikube"])
    assert result.exit_code == 0


@pytest.mark.skipif(sys.version_info < (3, 11), reason="requires python3.11 or later")
def test_check_docker_desktop():
    result = runner.invoke(cli, ["check", "--target", "docker-desktop"])
    assert result.exit_code == 0


@pytest.mark.skipif(sys.version_info < (3, 11), reason="requires python3.11 or later")
def test_install_on_kubernetes():
    result = runner.invoke(
        cli,
        [
            "install",
            "-k",
            "--data-load-flag",
            "dd-reference",
            "--force",
        ],
    )
    assert result.exit_code == 0


@pytest.mark.parametrize(
    "test_input",
    [
        ("list-pods"),
        ("services"),
        ("ready"),
        ("ingress"),
        ("client-secret"),
        ("post-message"),
        ("helm-list"),
        ("docker-info"),
        ("cpu"),
    ],
)
def test_diag_commands(test_input):
    result = runner.invoke(cli, ["diag", test_input])
    assert result.exit_code == 0, f"exit status, stdout: {result.stdout}"


@pytest.mark.skipif(sys.version_info < (3, 11), reason="requires python3.11 or later")
@pytest.mark.parametrize(
    "test_input",
    [
        ("token"),
        ("refresh-token"),
        ("list-clients"),
        ("list-users"),
        ("legal-tags"),
        ("groups"),
        ("info"),
        ("search"),
    ],
)
def test_commands(test_input):
    result = runner.invoke(cli, [test_input])
    assert result.exit_code == 0, f"exit status, stdout: {result.stdout}"


@pytest.mark.skipif(sys.version_info < (3, 11), reason="requires python3.11 or later")
@pytest.mark.skipif(sys.version_info < (3, 11), reason="requires python3.11 or later")
def test_status():
    result = runner.invoke(cli, ["status", "--threshold", "5"])
    assert result.exit_code == 0


@pytest.mark.skipif(sys.version_info < (3, 11), reason="requires python3.11 or later")
def test_cleanup():
    result = runner.invoke(cli, ["delete", "--force"])
    assert result.exit_code == 0
