import numpy as np

from prisma import Prisma
from python.embeddings.ann_faiss import AnnFaiss
from python.embeddings.embedding import Embedding
from python.embeddings.embedding_link_index import EmbeddingLinkIndex


class AnnSearch:
    def __init__(self, db: Prisma, datasource_id: int, index_number: int, path: str):
        self.index = AnnFaiss()
        self.index.load(path)
        self.embedding_link_index = EmbeddingLinkIndex(path)
        self.embedding_link_index.load()

        self.db = db
        self.index_number = index_number

        self.datasource_id = datasource_id

    def lookup_link(self, index: int):
        table_id_column_id_and_value = self.embedding_link_index.query(index)

        return table_id_column_id_and_value

    def search(self, embedding, number_of_matches):
        scores, results = self.index.query(embedding, number_of_matches)

        reject_idxs = results == -1
        scores = np.delete(scores, reject_idxs, axis=1)
        results = np.delete(results, reject_idxs)

        scores_results = []
        for (score, idx) in zip(scores.tolist()[0], results.tolist()):
            if idx != -1:
                scores_results.append((score, self.lookup_link(idx)))

        return scores_results
