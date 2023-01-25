import os

import numpy as np
import openai
from backoff_utils import apply_backoff
from decouple import config

openai.api_key = config("OPENAI_KEY")


class OpenAIEmbeddings:
    @apply_backoff(max_tries=5)
    def encode(content: str):
        result = openai.Embedding.create(model="text-embedding-ada-002", input=content)

        emb = np.array(result.data[0].embedding, dtype=np.float32)
        return emb
