from python.embeddings.ann_faiss import AnnFaiss
from python.embeddings.embedding import Embedding


class AnnSearch:
    def __init__(self, index_number: int, path: str):
        self.index = AnnFaiss()
        self.index.load(path)

    def search(self, embedding, number_of_matches):
        result = self.index.query(embedding, number_of_matches)
        print(result)
