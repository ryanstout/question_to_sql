# isort: skip_file
# fmt: off

# NOTE order of operations really matters here!
import os
os.environ["PYTHON_ENV"] = "test"

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from python.setup import log

import pytest


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "filter_headers": [
            "Authorization"
            # headers with random IDs which cause requests not to match, exclude these
            # "Date",
        ],
        # "filter_query_parameters": ["signature", "timestamp"],
        "decode_compressed_response": True,
        "ignore_localhost": True,
        # if libraries use `ping` or something similar, this reduces duplicate recordings
        # "allow_playback_repeats": True,
    }
# wipe redis on each run: make sure you are using a separate redis from dev!
from python.utils.redis import application_redis_connection
redis = application_redis_connection()

@pytest.fixture(scope="function", autouse=True)
def wipe_redis_and_database():
    redis.flushall()

from python.server import application
@pytest.fixture()
def app():
    return application
