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
        self.idx_table_names = AnnSearch(db, datasource_id, 0, f"python/indexes/{datasource.id}/table_names")
        self.idx_column_names = AnnSearch(db, datasource_id, 1, f"python/indexes/{datasource.id}/column_names")
        self.idx_table_and_column_names = AnnSearch(db, datasource_id, 3, f"python/indexes/{datasource.id}/table_and_column_names")

        # Table and Columns indexes
        # self.idx_table_and_column_names_and_values = AnnSearch(
        #     db, datasource_id, 4, f"python/indexes/{datasource.id}/table_and_column_names_and_values")
        self.idx_column_name_and_all_column_values = AnnSearch(
            db, datasource_id, 5, f"python/indexes/{datasource.id}/column_name_and_all_column_values"
        )

        # Cell values
        self.idx_values = AnnSearch(self.db, datasource_id, 2, f"python/indexes/{datasource.id}/values")

    def rank(self, query: str, embedder=OpenAIEmbeddings, cache_results=True, weights=[1.0, 1.0, 1.0, 1.0, 1.0]):

        rankings = {}

        query_embedding = Embedding(self.db, query, embedder=embedder, cache_results=cache_results).embedding_numpy

        # Fetch ranked table id
        table_matches = self.idx_table_names.search(query_embedding, 1000)
        tables_with_columns_matches = self.idx_column_names.search(query_embedding, 1000)

        tables = self.merge_ranks([table_matches, tables_with_columns_matches], weights[:2], 0)

        for table_id in self.pull_assoc(tables, 0):
            rankings[table_id] = {}

        columns_matches = self.idx_column_names.search(query_embedding, 100000)
        column_name_and_all_column_values_matches = self.idx_column_name_and_all_column_values.search(query_embedding, 100000)

        columns = self.merge_ranks([columns_matches, column_name_and_all_column_values_matches], weights[2:4], 1)

        # Assign the column ids
        for column in columns:
            column_table_id = column[1][0]
            if column_table_id in rankings:
                rankings[column_table_id][column[1][1]] = []

        # Get values from indexes
        value_matches = self.idx_values.search(query_embedding, 10000)

        # Assign the value matches for each associated column
        for value_match in value_matches:
            table_id, column_id, value = value_match[1]
            rankings[table_id][column_id].append(value)

        print("tables: ", rankings)

    def merge_ranks(self, scores_and_associations, weights, remove_dups_idx=None):
        # Merge the output of multiple AnnSearch#search's via the passed in
        # weights
        print(remove_dups_idx)

        merged = []
        for idx, scores_and_assocs in enumerate(scores_and_associations):
            for score_and_assoc in scores_and_assocs:
                # Multiply the scores by the the associated weight
                merged.append((score_and_assoc[0] * weights[idx], score_and_assoc[1]))

        # Sort
        merged.sort(key=lambda x: x[0], reverse=True)

        if remove_dups_idx is not None:
            # Remove duplicates for the target table, column, or value
            final = []
            seen = set()
            for score_and_assoc in merged:
                if score_and_assoc[1][remove_dups_idx] not in seen:
                    final.append(score_and_assoc)
                    seen.add(score_and_assoc[1][remove_dups_idx])
        else:
            final = merged

        return final

    def pull_assoc(self, scores_and_assocs, assoc_idx):
        # Grabs the table, column, or value from the association tuple
        return [score_and_assoc[1][assoc_idx] for score_and_assoc in scores_and_assocs]


if __name__ == "__main__":
    from python.utils.connections import Connections

    connections = Connections()
    connections.open()

    datasource = connections.db.datasource.find_first()

    Ranker(connections.db, datasource.id).rank("how many orders from Montana?")
