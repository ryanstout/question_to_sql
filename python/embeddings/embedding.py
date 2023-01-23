# Wrappers the openai embedding API and db cache
import openai
import os
import numpy as np
from numpy.lib.npyio import NpzFile
import pickle

import xxhash
from decouple import config
import io
from prisma import Base64


openai.api_key = config('OPENAI_KEY')


class Embedding:
    def __init__(self, db, content):
        # Hash the content
        hash = self.hash(content)

        # Check if the embedding is already in the embedding cache
        embedding = db.embeddingcache.find_first(where={'contentHash': hash})

        if embedding:
            # Prisma requires things go through base64 to a Bytes (Blob) field. Because reasons?
            emb_load = io.BytesIO(Base64.decode(embedding.embedding))
            emb_load.seek(0)
            self.embedding_numpy = np.load(emb_load, allow_pickle=True)['x']

            self.content_hash = embedding.contentHash
        else:

            # Get embedding of content from openai
            embedding = self.openai_embedding(content)

            # Serialize it to npz
            emb_str = io.BytesIO()
            np.savez_compressed(emb_str, x=embedding, allow_pickle=True)
            emb_bytes = emb_str.getvalue()

            # Cache the embedding
            db.embeddingcache.create(data={
                'contentHash': hash,
                # why prisma won't let me pass in bytes is beyond me
                'embedding': Base64.encode(emb_bytes)
            })

            self.embedding_numpy = embedding
            self.content_hash = hash

    def hash(self, content):
        # xxhash has good properties for small strings and a nice trade off
        # between performance and collision resistance
        return xxhash.xxh64(content).hexdigest()

    def openai_embedding(self, content):
        result = openai.Embedding.create(
            model="text-embedding-ada-002",
            input=content
        )

        emb = np.array(result.data[0].embedding, dtype=np.float32)
        return emb


if __name__ == "__main__":
    from prisma import Prisma
    db = Prisma()
    db.connect()
    e = Embedding(db, "hello world")
    print(e.embedding_numpy)
