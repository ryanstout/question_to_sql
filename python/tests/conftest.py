from python.setup import log

import pytest

from python.server import application


@pytest.fixture()
def app():
    return application
