# content of conftest.py

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )
    parser.addoption(
        "--install", action="store_true", default=False, help="run install tests"
    )
    parser.addoption(
        "--delete", action="store_true", default=False, help="run delete tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")
    config.addinivalue_line("markers", "install: mark test as install")
    config.addinivalue_line("markers", "delete: mark test as delete")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    if config.getoption("--install"):
        # --install given in cli: do not skip install tests
        return
    if config.getoption("--delete"):
        # --delete given in cli: do not skip delete tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    skip_install = pytest.mark.skip(reason="need --install option to run")
    skip_delete = pytest.mark.skip(reason="need --delete option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
        if "install" in item.keywords:
            item.add_marker(skip_install)
        if "delete" in item.keywords:
            item.add_marker(skip_delete)
