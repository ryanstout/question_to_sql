import numpy as np

from python.embeddings.ann_faiss import AnnFaiss
from python.embeddings.embedding_link_index import EmbeddingLinkIndex
from python.sql.types import DbElementIds


class AnnSearch:
    def __init__(self, path: str):
        self.index = AnnFaiss()
        self.index.load(path)

        self.embedding_link_index = EmbeddingLinkIndex(path)
        self.embedding_link_index.load()

    def lookup_link(self, index: int) -> DbElementIds:
        table_id_column_id_and_value = self.embedding_link_index.query(index)

        return table_id_column_id_and_value

    def search(self, embedding, number_of_matches: int) -> list[tuple[float, DbElementIds]]:
        scores, results = self.index.query(embedding, number_of_matches)

        reject_idxs = results == -1
        scores = np.delete(scores, reject_idxs, axis=1)
        results = np.delete(results, reject_idxs)

        scores_results = []
        for (score, idx) in zip(scores.tolist()[0], results.tolist()):
            if idx != -1:
                db_element_ids = self.lookup_link(idx)
                scores_results.append((score, db_element_ids))

        return scores_results
