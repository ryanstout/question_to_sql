from python.setup import log

import os

import backoff
import numpy as np
import openai
from decouple import config

openai.api_key = config("OPENAI_KEY")

from openai.error import OpenAIError


class OpenAIEmbeddings:
    # https://github.com/litl/backoff/issues/92
    @backoff.on_exception(backoff.expo, OpenAIError, factor=60, max_tries=5)
    def encode(content: str):
        log.debug("encoding with OpenAI", content=content)

        result = openai.Embedding.create(model="text-embedding-ada-002", input=content)

        emb = np.array(result.data[0].embedding, dtype=np.float32)
        return emb
