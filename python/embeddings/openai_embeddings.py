from python.setup import log

import os

import numpy as np
from openai.error import OpenAIError

from python.utils.logging import log
from python.utils.openai_rate_throttled import openai_throttled


class OpenAIEmbeddings:
    def encode(content: str):
        log.debug("encoding with OpenAI", content=content)

        result = openai_throttled.embed(model="text-embedding-ada-002", input=content)

        return result
