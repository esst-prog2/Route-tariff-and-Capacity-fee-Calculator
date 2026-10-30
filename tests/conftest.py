"""The app's default tariff file is the real export; the existing tests and
their figures are built on the synthetic sample, so every test runs with the
sample configured unless it points the variable somewhere else itself."""

import pytest

from core import tariffs


@pytest.fixture(autouse=True)
def sample_tariff_file(monkeypatch):
    monkeypatch.setenv(tariffs.PATH_ENV_VAR, str(tariffs.DEFAULT_SAMPLE_PATH))


def pytest_configure(config):
    config.addinivalue_line("markers", "excel: recalculates the Capacity Fee Workbook in Excel (run with -m excel)")


def pytest_collection_modifyitems(config, items):
    """The Excel check takes minutes, so it runs only when asked for with `-m excel`."""
    if "excel" in (config.getoption("markexpr") or ""):
        return
    skip = pytest.mark.skip(reason="the Excel check runs with `pytest -m excel`")
    for item in items:
        if "excel" in item.keywords:
            item.add_marker(skip)
