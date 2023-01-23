from python.embeddings.ann_faiss import AnnFaiss


class AnnSearch:
    def __init__(self, index_number: int, path: str):
        self.index = AnnFaiss().load(self.path)

    def search(self):
