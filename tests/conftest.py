"""The app's default tariff file is the real export; the existing tests and
their figures are built on the synthetic sample, so every test runs with the
sample configured unless it points the variable somewhere else itself."""

import pytest

from core import tariffs


@pytest.fixture(autouse=True)
def sample_tariff_file(monkeypatch):
    monkeypatch.setenv(tariffs.PATH_ENV_VAR, str(tariffs.DEFAULT_SAMPLE_PATH))
