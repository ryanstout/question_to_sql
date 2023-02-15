import io
from typing import Type

import numpy as np
import xxhash

from python.embeddings.msmacro_embedder import MSMarcoEmbedder
from python.embeddings.openai_embedder import OpenAIEmbedder
from python.utils.db import application_database_connection

from prisma import Base64, Prisma

db = application_database_connection()

# create multiple embeddings vector via openai and store to disk.
# docs/prompt_embeddings.md for more information
class Embedding:
    # embedder: BaseEmbedder

    def __init__(self, content_str: str, embedder: OpenAIEmbedder | MSMarcoEmbedder, cache_results=True):
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


# TODO should move this into a test
if __name__ == "__main__":
    e = Embedding("hello world", embedder=OpenAIEmbedder)
    print(e.embedding_numpy)
