import os
from typing import Union
import numpy as np

from python.embeddings.embedding import Embedding
from python.embeddings.ann_faiss import AnnFaiss


class AnnIndex:
    def __init__(self, db, index_number: int, path: str):
        self.path = path
        self.db = db
        self.index_number = index_number
        self.index_offset = 0
        self.embeddings = []

    def add(self, content: str, tableId: Union[int, None], columnId: Union[int, None], value: Union[str, None]):
        embedding = Embedding(self.db, content)

        # Create a EmbeddingLink
        embedding_link = self.db.embeddinglink.create(data={
            'indexNumber': self.index_number,
            'indexOffset': self.index_offset,
            'contentHash': embedding.content_hash,
            'tableId': tableId,
            'columnId': columnId,
            'value': value
        })

        self.embeddings.append(embedding.embedding_numpy)

        self.index_offset += 1

    def save(self):
        embed_size = len(self.embeddings)
        print("Embedding len: ", embed_size)

        if embed_size > 0:
            data = np.stack(self.embeddings, axis=0)

            # Make output folder if it doesn't exist
            os.makedirs(os.path.dirname(self.path), exist_ok=True)

            print(data.dtype, data.shape)
            AnnFaiss().build_and_save(data, self.path)
