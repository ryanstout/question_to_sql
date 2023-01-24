# Taking in the question, generate the following data structure to pass to
# the schema builder:
#
# {
#     'tableId1': {
#         'columnId1': ['valueHint1', 'valueHint2'],
#         'columnId2': [],
#         'columnId3': ['valueHint1', 'valueHint2', 'valueHint3'],
#     },
#     'tableId2': {
#         # ...
#     },
#     # ...
# }

from python.embeddings.ann_search import AnnSearch
from python.embeddings.openai_embeddings import OpenAIEmbeddings
from python.embeddings.embedding import Embedding
import numpy as np


class Ranker:
    def __init__(self, db, datasource_id: int):
        self.db = db

        # Load the faiss indexes
        self.idx_table_names = AnnSearch(
            db, datasource_id, 0, f"python/indexes/{datasource.id}/table_names")
        self.idx_column_names = AnnSearch(
            db, datasource_id, 1, f"python/indexes/{datasource.id}/column_names")
        self.idx_table_and_column_names = AnnSearch(
            db, datasource_id, 3, f"python/indexes/{datasource.id}/table_and_column_names")

        # Table and Columns indexes
        # self.idx_table_and_column_names_and_values = AnnSearch(
        #     db, datasource_id, 4, f"python/indexes/{datasource.id}/table_and_column_names_and_values")
        self.idx_column_name_and_all_column_values = AnnSearch(
            db, datasource_id, 5, f"python/indexes/{datasource.id}/column_name_and_all_column_values")

    def rank(self, query: str, embedder=OpenAIEmbeddings, cache_results=True):
        query_embedding = Embedding(
            self.db, query, embedder=embedder, cache_results=cache_results).embedding_numpy

        # Fetch ranked table id
        scores_and_tables = self.idx_table_names.search(query_embedding, 1000)
        scores_and_tables_with_columns = self.idx_column_names.search(
            query_embedding, 1000)


if __name__ == '__main__':
    from python.utils.connections import Connections

    connections = Connections()
    connections.open()

    datasource = connections.db.datasource.find_first()

    Ranker(connections.db, datasource.id).rank("how many orders from Montana?")
