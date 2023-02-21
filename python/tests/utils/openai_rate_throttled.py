from unittest.mock import patch

import openai.error
import pytest

from python.utils.openai_rate_throttled import (
    BACKOFF_MAX_RETRIES,
    OPENAI_THROTTLED,
    all_retryable_openai_errors,
)

# TODO we should see if we can rename `python` to `knolbe` in the future AND make it play well with linters and such
# import sys
# sys.modules["knolbe"] = python
# from knolbe.utils.openai_rate_throttled import (
#     OPENAI_THROTTLED,
#     all_retryable_openai_errors,
# )


def test_openai_error_inspection():
    error_class_list = all_retryable_openai_errors()

    # ensure that the list looks sane; this is not exhaustive
    assert len(error_class_list) > 0
    assert openai.error.RateLimitError in error_class_list


@patch(
    "openai.Embedding.create",
    side_effect=openai.error.RateLimitError("a bad error"),
    # the backoff library uses the __name__, which is the fqn of the function, as part of the logger
    __name__="openai.Embedding.create",
)
@patch("python.utils.openai_rate_throttled.BACKOFF_RETRY_BASE", 0.1)
def test_backoff(openai_embedding_create):
    embed_call_args = {"input": "hello world"}

    with pytest.raises(openai.error.RateLimitError):
        OPENAI_THROTTLED.embed(**embed_call_args)

    assert openai_embedding_create.call_count == BACKOFF_MAX_RETRIES
    assert openai_embedding_create.call_args.kwargs == embed_call_args
