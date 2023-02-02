import os
from threading import Lock
from typing import Union

import numpy as np

from prisma import Prisma
from python.embeddings.ann_faiss import AnnFaiss
from python.embeddings.embedding import Embedding
from python.embeddings.embedding_link_index import EmbeddingLinkIndex
from python.utils.logging import log


# ann = approximate nearest neighbor
class AnnIndex:
    def __init__(self, db: Prisma, index_number: int, path: str):
        self.path = path
        self.db = db
        self.index_number = index_number
        self.index_offset = 0
        self.embeddings = []
        self.lock = Lock()

        self.embedding_link_index = EmbeddingLinkIndex(path)

    def add(
        self,
        datasource_id: int,
        content: str,
        table_id: Union[int, None],
        column_id: Union[int, None],
        value: Union[str, None],
    ):
        log.debug("Vector for ", content=content)
        embedding = Embedding(self.db, content)

        # Needs the mutex to prevent parallel columns from adding to it at the
        # same time. The index_offset is important for the vector indexing.
        self.lock.acquire()

        previous_offset = self.index_offset

        self.embedding_link_index.add(previous_offset, table_id, column_id, value)

        self.embeddings.append(embedding.embedding_numpy)

        self.index_offset += 1

        self.lock.release()

    def save(self):
        embed_size = len(self.embeddings)
        log.debug(f"Build for index #{self.index_number}: ", embed_size=embed_size)

        if embed_size > 0:
            data = np.stack(self.embeddings, axis=0)

            # Make output folder if it doesn't exist
            os.makedirs(os.path.dirname(self.path), exist_ok=True)

            self.embedding_link_index.save()

            log.debug("Build Faiss Index: ", dtype=data.dtype, size=data.shape)
            AnnFaiss().build_and_save(data, self.path)
