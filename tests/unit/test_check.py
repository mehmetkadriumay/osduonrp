import sys
import pytest
from typer.testing import CliRunner
from cibutler.main import cli

runner = CliRunner()


@pytest.mark.skipif(sys.version_info < (3, 11), reason="requires python3.11 or later")
@pytest.mark.skip(reason="no way of currently testing this as part of pipeline")
def test_check():
    result = runner.invoke(cli, ["check"])
    if result.exit_code == 2:
        pytest.skip("Not supported env")
    assert result.exit_code == 0
