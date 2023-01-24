import openai
import os
import numpy as np
from decouple import config


openai.api_key = config("OPENAI_KEY")


class OpenAIEmbeddings:
    def encode(content: str):
        result = openai.Embedding.create(model="text-embedding-ada-002", input=content)

        emb = np.array(result.data[0].embedding, dtype=np.float32)
        return emb
