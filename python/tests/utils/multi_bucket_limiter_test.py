import time
from unittest import mock

import pytest

from python.utils.multi_bucket_limiter import MultiBucketLimiter

sleeps = []


def sleep_side_effect(duration: int):
    sleeps.append(duration)


def test_can_bucket_limiter_limit():
    sleeps.clear()
    with mock.patch("time.sleep", mock.MagicMock(return_value=None, side_effect=sleep_side_effect)):
        with mock.patch("time.time", mock.MagicMock(return_value=0)):
            limiter = MultiBucketLimiter({"requests": 2, "tokens": 10})

            # Make two requests to pass the rate limit
            with limiter.request_when_available({"requests": 1, "tokens": 0}):
                0
            with limiter.request_when_available({"requests": 1, "tokens": 0}):
                0
        with mock.patch("time.time", mock.MagicMock(return_value=0)):
            with limiter.request_when_available({"requests": 1, "tokens": 0}):
                0

        with mock.patch("time.time", mock.MagicMock(return_value=30)):
            with limiter.request_when_available({"requests": 1, "tokens": 0}):
                0

        with mock.patch("time.time", mock.MagicMock(return_value=120)):
            with limiter.request_when_available({"requests": 1, "tokens": 0}):
                0

    assert sleeps == [30.0, 60.0]


def test_bucket_limiter_warns_about_single_request_using_more_than_max():
    with pytest.raises(ValueError):
        limiter = MultiBucketLimiter({"requests": 2, "tokens": 10})
        with limiter.request_when_available({"requests": 1, "tokens": 20}):
            20


def test_can_bucket_limiter_multi_limit():
    sleeps.clear()
    with mock.patch("time.sleep", mock.MagicMock(return_value=None, side_effect=sleep_side_effect)):
        with mock.patch("time.time", mock.MagicMock(return_value=0)):
            limiter = MultiBucketLimiter({"requests": 2, "tokens": 10})

            # Make two requests to pass the rate limit
            with limiter.request_when_available({"requests": 1, "tokens": 6}):
                6
            with limiter.request_when_available({"requests": 1, "tokens": 6}):
                6

    assert sleeps == [12.0]
