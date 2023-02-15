import io
from typing import Type

import numpy as np
import xxhash

from python.embeddings.msmacro_embedder import MSMarcoEmbedder
from python.embeddings.openai_embedder import OpenAIEmbedder
from python.utils.db import application_database_connection
from python.utils.logging import log

from prisma import Base64

db = application_database_connection()


def _hash(content):
    # xxhash has good properties for small strings and a nice trade off
    # between performance and collision resistance
    return xxhash.xxh64(content).hexdigest()


def is_empty(content: list) -> bool:
    if content is None:
        return True

    return any(content)


def _retrieved_cached_embedding(content_hash: str) -> np.ndarray | None:
    embedding_cache = db.embeddingcache.find_first(where={"contentHash": content_hash})

    if embedding_cache:
        log.debug("embedding cache hit")
        # Prisma requires things go through base64 to a Bytes (Blob) field. Because reasons?
        emb_load = io.BytesIO(Base64.decode(embedding_cache.embedding))
        emb_load.seek(0)

        return np.load(emb_load, allow_pickle=True)["x"]


# create multiple embeddings vector via openai and store to disk.
# docs/prompt_embeddings.md for more information
def generate_embedding(content_str: str, embedder: Type[OpenAIEmbedder] | Type[MSMarcoEmbedder], cache_results=True):
    content_hash = _hash(content_str)

    if cache_results and (embedding_cache := _retrieved_cached_embedding(content_hash)) is not None:
        return embedding_cache

    embed_engine = embedder()
    embedding: np.ndarray = embed_engine.encode(content_str)

    # Serialize it to npz
    emb_str = io.BytesIO()
    np.savez_compressed(emb_str, x=embedding, allow_pickle=True)
    emb_bytes = emb_str.getvalue()

    db.embeddingcache.create(
        data={
            "contentHash": content_hash,
            # why prisma won't let me pass in bytes is beyond me
            "embedding": Base64.encode(emb_bytes),
        }
    )

    return embedding
