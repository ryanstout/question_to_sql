import redis
from decouple import config

from python.utils.environments import is_testing

REDIS = None


def application_redis_connection():
    global REDIS  # pylint: disable=global-statement

    if REDIS is None:
        redis_url = config("TEST_REDIS_URL") if is_testing() else config("REDIS_URL")
        assert isinstance(redis_url, str)

        REDIS = redis.from_url(redis_url)

    return REDIS
