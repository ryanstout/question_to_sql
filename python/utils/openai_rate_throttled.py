# A wrapper around the OpenAI API that integrates the rate limit throttling
# into everything.
#
# This module exports a singleton, use as follows:
#
# from python.utils.openai_rate_throttled import openai_throttled
#
# openai_throttled.complete("Hello, world!")

import inspect
import typing as t
from contextlib import contextmanager

import backoff
import numpy as np
import openai
import openai.error
from decouple import config
from openai.error import OpenAIError

from python.utils.batteries import log_execution_time
from python.utils.logging import log
from python.utils.tokens import count_tokens

from .multi_bucket_limiter import MultiBucketLimiter

openai.api_key = config("OPENAI_KEY")


# there's lots of different error types, and more can be added
def all_retryable_openai_errors() -> list[t.Type[OpenAIError]]:
    all_errors = [c[1] for c in inspect.getmembers(openai.error, inspect.isclass)]
    openai_error_subclasses = [
        cls for cls in all_errors if issubclass(cls, openai.error.OpenAIError) and cls != openai.error.OpenAIError
    ]

    # remove errors we do not want to backoff
    openai_error_subclasses.remove(openai.error.SignatureVerificationError)
    openai_error_subclasses.remove(openai.error.InvalidAPIType)
    openai_error_subclasses.remove(openai.error.AuthenticationError)
    openai_error_subclasses.remove(openai.error.PermissionError)

    return openai_error_subclasses


class ChoicesItem(t.TypedDict):
    finish_reason: str
    index: int
    logprobs: None
    text: str


# usage fields change depending on which endpoint you call
class OpenAIUsage(t.TypedDict):
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int


# NOTE we are are cheating here: OpenAIObject is a subclass of dict which adds dot-notion accessors
#      it's easier to type if we just treat them as dicts
class OpenAICompletionResponse(t.TypedDict):
    choices: list[ChoicesItem]
    created: int
    id: str
    model: str
    object: str
    usage: OpenAIUsage


class EmbeddingData(t.TypedDict):
    embedding: list[float]
    index: int
    object: str


class OpenAIEmbeddingResponse(t.TypedDict):
    data: list[EmbeddingData]
    model: str
    object: str
    usage: OpenAIUsage


def _base_consumption_request():
    return {"requests": 1, "codex_tokens": 0, "embed_tokens": 0}


# pylint: disable=pointless-string-statement
"""
You cannot use a backoff decorator with a context manager:
    https://github.com/litl/backoff/issues/18#issuecomment-297772840

To get around this, we create a decorator function with all of the params we need,
and then wrap individual functions.

TODO in the future we can include this directly in the context manager in the class,
but I've spent enough time on this problem already at this point.

TODO the numbers here are just guesses, feel free to change them
"""
BACKOFF_MAX_RETRIES = 5
BACKOFF_RETRY_BASE = 60


# we don't cache the decorator result because it allows us to patch the config values for testing
def _backoff_decorator(func: t.Callable) -> t.Callable:
    return backoff.on_exception(
        # TODO consider adding min delay https://github.com/litl/backoff/issues/92
        wait_gen=backoff.expo,
        exception=tuple(all_retryable_openai_errors()),
        # how much each exponential backoff should increase the time by
        # https://github.com/litl/backoff/blob/d82b23c42d7a7e2402903e71e7a7f03014a00076/backoff/_wait_gen.py#L9-L10
        factor=BACKOFF_RETRY_BASE,
        # TODO should we just set this to an insane value since some of these operations are very hard to retry
        #      maybe this makes sense if we set a process-level timeout for the web server side of things
        max_tries=BACKOFF_MAX_RETRIES,
        # NOTE the logger logic is actually pretty intense within `@backoff`, I'm not sure what's going on there yet,
        #      so let's use the default logger for now
        # logger=log,
    )(func)


class OpenAIThrottled:
    def __init__(
        self,
        # https://platform.openai.com/docs/guides/rate-limits/overview
        max_requests_per_minute: int = 20,
        max_codex_tokens_per_minute: int = 40_000,
        max_embed_tokens_per_minute: int = 250_000,
    ):
        self.limiter = MultiBucketLimiter(
            {
                "requests": max_requests_per_minute,
                "codex_tokens": max_codex_tokens_per_minute,
                "embed_tokens": max_embed_tokens_per_minute,
            }
        )

    def complete(self, **kwargs):
        # Called in a with statement, blocks via time.sleep until the resources
        # needed for the next request are available. The return value from the
        # inside of the with should be the number of tokens consumed (in the
        # response of the API calls.) This helps keep track of actual
        # consumption, which can vary from the number of tokens requested.

        # add padding to handle max response
        # TODO is there a reason we shouldn't add this padding to the embedding as well?
        token_count = count_tokens(kwargs["prompt"]) + 1024
        completion_call = _backoff_decorator(openai.Completion.create)

        with self._safe_api_request(_base_consumption_request() | {"codex_tokens": token_count}):
            # TODO should make this more generic and avoid tying to completion directly
            result = completion_call(**kwargs)

        result = t.cast(OpenAICompletionResponse, result)

        total_tokens = result["usage"]["total_tokens"]

        if total_tokens != token_count:
            log.info(
                "incorrect token estimate", method="completion", total_tokens=total_tokens, guess_tokens=token_count
            )

        self.limiter.consume_resources(_base_consumption_request() | {"codex_tokens": total_tokens})

        return result

    def embed(self, **kwargs):
        token_count = count_tokens(kwargs["input"])
        embedding_call = _backoff_decorator(openai.Embedding.create)

        with self._safe_api_request(_base_consumption_request() | {"embed_tokens": token_count}):
            result = embedding_call(**kwargs)

        result = t.cast(OpenAIEmbeddingResponse, result)

        total_tokens = result["usage"]["total_tokens"]
        self.limiter.consume_resources(_base_consumption_request() | {"embed_tokens": total_tokens})

        embedding_list = result["data"]
        assert len(embedding_list) == 1, "expected exactly one embedding"

        # TODO this sort of logic should be handled up the stack
        emb = np.array(embedding_list[0]["embedding"], dtype=np.float32)

        return emb

    @contextmanager
    def _safe_api_request(self, consumption_request):
        with self.limiter.request_when_available(consumption_request):
            with log_execution_time("openai completion"):
                yield


# TODO should uppercase if it is a constant?
openai_throttled = OpenAIThrottled()
OPENAI_THROTTLED = openai_throttled
