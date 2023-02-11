# Wrappers the openai embedding API and db cache
import io
from typing import Type

import numpy as np
import xxhash

from python.embeddings.base_embedder import BaseEmbedder

from prisma import Base64, Prisma


# create embeddings vector via openai from a string
class Embedding:
    embedder: BaseEmbedder

    def __init__(self, db: Prisma, content_str: str, embedder: Type[BaseEmbedder] = BaseEmbedder, cache_results=True):
        self.embedder = embedder()
        self.cache_results = cache_results

        # Hash the content
        content_hash = self.hash(content_str)

        if cache_results:
            # Check if the embedding is already in the embedding cache
            embedding_cache = db.embeddingcache.find_first(where={"contentHash": content_hash})

            if embedding_cache:
                # Prisma requires things go through base64 to a Bytes (Blob) field. Because reasons?
                emb_load = io.BytesIO(Base64.decode(embedding_cache.embedding))
                emb_load.seek(0)

                self.embedding_numpy = np.load(emb_load, allow_pickle=True)["x"]
                self.content_hash = embedding_cache.contentHash
                return None

        # Get embedding of content from openai
        embedding: np.ndarray = self.embedder.encode(content_str)

        # Serialize it to npz
        emb_str = io.BytesIO()
        np.savez_compressed(emb_str, x=embedding, allow_pickle=True)
        emb_bytes = emb_str.getvalue()

        # Cache the embedding
        db.embeddingcache.create(
            data={
                "contentHash": content_hash,
                # why prisma won't let me pass in bytes is beyond me
                "embedding": Base64.encode(emb_bytes),
            }
        )

        self.embedding_numpy = embedding
        self.content_hash = content_hash

    def hash(self, content):
        # xxhash has good properties for small strings and a nice trade off
        # between performance and collision resistance
        return xxhash.xxh64(content).hexdigest()


if __name__ == "__main__":
    _db = Prisma()
    _db.connect()
    e = Embedding(_db, "hello world")
    print(e.embedding_numpy)
