# A wrapper around the OpenAI API that integrates the rate limit throttling
# into everything.
#
# This module exports a singleton, use as follows:
#
# from python.utils.openai_rate_throttled import openai_throttled
#
# openai_throttled.complete("Hello, world!")


from python.setup import log

import time
import typing as t

import numpy as np
import openai
from decouple import config
from openai.error import OpenAIError

from python.utils.logging import log
from python.utils.tokens import count_tokens

from .multi_bucket_limiter import MultiBucketLimiter

openai.api_key = config("OPENAI_KEY")


class ChoicesItem(t.TypedDict):
    finish_reason: str
    index: int
    logprobs: None
    text: str


class Usage(t.TypedDict):
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int


class OpenAIResponse(t.TypedDict):
    choices: t.List[ChoicesItem]
    created: int
    id: str
    model: str
    object: str
    usage: Usage


class OpenAIThrottled:
    def __init__(
        self,
        max_requests_per_minute: float = 20,
        max_codex_tokens_per_minute: float = 40000,
        max_embed_tokens_per_minute: float = 250000,
        max_attempts: int = 5,
    ):
        self.max_attempts = max_attempts
        self.limiter = MultiBucketLimiter(
            {
                "requests": max_requests_per_minute,
                "codex_tokens": max_codex_tokens_per_minute,
                "embed_tokens": max_embed_tokens_per_minute,
            }
        )

    def complete(self, prompt: str, **kwargs):
        # Called in a with statement, blocks via time.sleep until the resources
        # needed for the next request are available. The return value from the
        # inside of the with should be the number of tokens consumed (in the
        # response of the API calls.) This helps keep track of actual
        # consumption, which can vary from the number of tokens requested.

        token_count = count_tokens(prompt) + 1024  # add padding to handle max response

        with self.limiter.request_when_available({"requests": 1, "codex_tokens": token_count, "embed_tokens": 0}):
            t1 = time.time()

            result = openai.Completion.create(
                prompt=prompt,
                **kwargs
                # engine="code-davinci-002",
                # max_tokens=1024,  # was 256
                # temperature=0.0,
                # top_p=1,
                # presence_penalty=0,
                # frequency_penalty=0,
                # best_of=1,
                # # logprobs=4,
                # n=1,
                # stream=False,
                # # tells the model to stop generating a response when it gets to the end of the SQL
                # stop=[";", "\n\n"],
            )
            t2 = time.time()
            log.info(f"Got openai completion response in ", time=t2 - t1)

            result = t.cast(OpenAIResponse, result)

            # Count the consumed tokens and the request
            total_tokens = result.usage["total_tokens"]

            log.info("Completion tokens: ", total_tokens=total_tokens, guess_tokens=token_count)
            self.limiter.consume_resources({"requests": 1, "codex_tokens": total_tokens, "embed_tokens": 0})

            return result

    def embed(self, input: str, **kwargs):
        token_count = count_tokens(input)

        with self.limiter.request_when_available({"requests": 1, "codex_tokens": 0, "embed_tokens": token_count}):
            result = openai.Embedding.create(input=input, **kwargs)

            total_tokens = result["usage"]["total_tokens"]
            self.limiter.consume_resources({"requests": 1, "codex_tokens": total_tokens, "embed_tokens": 0})

            emb = np.array(result.data[0].embedding, dtype=np.float32)

            return emb


# Export singleton
openai_throttled = OpenAIThrottled(
    max_requests_per_minute=int(20 * 0.5),
    max_codex_tokens_per_minute=int(40000 * 0.3),
    max_embed_tokens_per_minute=int(250000 * 0.3),
)
