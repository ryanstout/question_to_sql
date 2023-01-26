from python.setup import log

import os

import backoff_utils
import numpy as np
import openai
from backoff_utils import apply_backoff, strategies
from decouple import config

openai.api_key = config("OPENAI_KEY")


class OpenAIEmbeddings:
    # https://backoff-utils.readthedocs.io/en/latest/strategies.html
    # if we've hit an openAI limit, we need to wait awhile
    @apply_backoff(max_tries=5, strategy=strategies.Exponential(minimum=60))
    def encode(content: str):
        log.debug("encoding with OpenAI", content=content)

        result = openai.Embedding.create(model="text-embedding-ada-002", input=content)

        emb = np.array(result.data[0].embedding, dtype=np.float32)
        return emb
