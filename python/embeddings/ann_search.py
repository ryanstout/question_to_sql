from python.embeddings.ann_faiss import AnnFaiss
from python.embeddings.embedding import Embedding
import numpy as np


class AnnSearch:
    def __init__(self, db, datasource_id: int, index_number: int, path: str):
        self.index = AnnFaiss()
        self.index.load(path)

        self.db = db
        self.index_number = index_number

        self.datasource_id = datasource_id

    def lookup_link(self, link_id: int):
        link = self.db.embeddinglink.find_first(where={
            'dataSourceId': int(self.datasource_id),
            'indexNumber': self.index_number,
            'indexOffset': int(link_id),
        })

        return [link.tableId, link.columnId, link.value]

    def search(self, embedding, number_of_matches):
        scores, results = self.index.query(embedding, number_of_matches)

        reject_idxs = (results == -1)
        scores = np.delete(scores, reject_idxs, axis=1)
        results = np.delete(results, reject_idxs)

        scores_results = []
        for (score, idx) in zip(scores.tolist()[0], results.tolist()):
            if idx != -1:
                scores_results.append((score, self.lookup_link(idx)))

        return scores_results
