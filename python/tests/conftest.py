# isort:skip_file
# NOTE order of operations really matters here!

import sys, os

from python.utils.redis import application_redis_connection

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from python.setup import log

import pytest

from python.server import application

os.environ["PYTHON_ENV"] = "testing"

redis = application_redis_connection()


@pytest.fixture()
def app():
    return application


@pytest.fixture(scope="function", autouse=True)
def wipe_redis_and_database():
    redis.flushall()
