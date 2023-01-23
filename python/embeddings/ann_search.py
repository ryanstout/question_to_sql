from python.embeddings.ann_faiss import AnnFaiss
from python.embeddings.embedding import Embedding


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

        print("LINK: ", link)
        return [link.tableId, link.columnId, link.value]

    def search(self, embedding, number_of_matches):
        results = self.index.query(embedding, number_of_matches)

        results = [i for i in results if i != -1]

        # map in tables, coulmns, values
        results = map(self.lookup_link, results)
        print(list(results))
