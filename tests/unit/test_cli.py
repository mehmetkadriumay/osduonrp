import sys
import pytest
from typer.testing import CliRunner
from cibutler.main import cli

runner = CliRunner()


@pytest.mark.skipif(sys.version_info < (3, 11), reason="requires python3.11 or later")
def test_show_completion():
    result = runner.invoke(cli, ["--show-completion"])
    if result.exit_code == 2:
        pytest.skip("Not supported env")
    assert result.exit_code == 0


def test_version():
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0


def test_version_command():
    result = runner.invoke(cli, ["version"])
    if result.exit_code == 3:
        pytest.skip("pip not installed")
    assert result.exit_code == 0
