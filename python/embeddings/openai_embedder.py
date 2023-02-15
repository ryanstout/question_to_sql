from python.setup import log

import numpy as np

from python.utils.openai_rate_throttled import openai_throttled


class OpenAIEmbedder:
    def encode(self, content_str: str) -> np.ndarray:
        log.debug("encoding with OpenAI", content=content_str)

        result = openai_throttled.embed(model="text-embedding-ada-002", input=content_str)

        return result
