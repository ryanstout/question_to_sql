from python.setup import log

import sys
import typing as t

import numpy as np

from python.embeddings.ann_search import AnnSearch
from python.embeddings.embedding import Embedding
from python.embeddings.openai_embeddings import OpenAIEmbeddings


# Taking in the question, generate the following data structure to pass to
# the schema builder:
class ElementRank(t.TypedDict):
    table_id: int
    column_id: t.Union[int, None]
    value_hint: t.Union[str, None]
    score: float


# note that in a ranking type list, you could have multiple ranking types with the same
# column_id and value_hints
SCHEMA_RANKING_TYPE = t.List[ElementRank]


class Ranker:
    def __init__(self, db, datasource_id: int):
        self.db = db

        # Load the faiss indexes
        self.idx_table_names = AnnSearch(db, datasource_id, 0, f"python/indexes/{datasource_id}/table_names")
        self.idx_column_names = AnnSearch(db, datasource_id, 1, f"python/indexes/{datasource_id}/column_names")
        self.idx_table_and_column_names = AnnSearch(db, datasource_id, 3, f"python/indexes/{datasource_id}/table_and_column_names")

        # Table and Columns indexes
        # self.idx_table_and_column_names_and_values = AnnSearch(
        #     db, datasource_id, 4, f"python/indexes/{datasource_id}/table_and_column_names_and_values")
        self.idx_column_name_and_all_column_values = AnnSearch(
            db, datasource_id, 5, f"python/indexes/{datasource_id}/column_name_and_all_column_values"
        )

        # Cell values
        self.idx_values = AnnSearch(self.db, datasource_id, 2, f"python/indexes/{datasource_id}/values")

    def rank(
        self,
        query: str,
        embedder=OpenAIEmbeddings,
        cache_results=True,
        table_weights=[1.0, 0.0, 0.1],
        column_weights=[0.1, 0.0, 0.0],
        value_weights=[1.0],
    ) -> SCHEMA_RANKING_TYPE:

        query_embedding = Embedding(self.db, query, embedder=embedder, cache_results=cache_results).embedding_numpy

        log.debug("Start faiss lookups")
        # Fetch ranked table id
        table_matches = self.idx_table_names.search(query_embedding, 1000)
        tables_with_columns_matches = self.idx_column_names.search(query_embedding, 1000)
        log.debug("Table matches", matches=table_matches)

        columns_matches = self.idx_column_names.search(query_embedding, 10000)
        column_name_and_all_column_values_matches = self.idx_column_name_and_all_column_values.search(query_embedding, 1000)
        log.debug("Column matches", matches=columns_matches)

        value_matches = self.idx_values.search(query_embedding, 1000)

        tables = self.merge_ranks([table_matches, tables_with_columns_matches, value_matches], table_weights, 0)
        columns = self.merge_ranks([columns_matches, column_name_and_all_column_values_matches, value_matches], column_weights, 1)
        values = self.merge_ranks([value_matches], value_weights, 2)

        log.debug("End faiss lookups")

        # rankings = list(map(lambda x: ElementRank(table_id=x[1][0], column_id=x[1][1], value_hint=x[1][2], score=x[0]), tables + columns + values))
        rankings = list(map(lambda x: ElementRank(table_id=x[1][0], column_id=x[1][1], value_hint=x[1][2], score=x[0]), tables + columns))

        # Sort rankings by score
        rankings.sort(key=lambda x: x["score"], reverse=True)

        return rankings

    def merge_ranks(self, scores_and_associations, weights, remove_dups_idx=None):
        # Merge the output of multiple AnnSearch#search's via the passed in
        # weights
        merged = []
        for idx, scores_and_assocs in enumerate(scores_and_associations):
            for score_and_assoc in scores_and_assocs:
                # Multiply the scores by the the associated weight
                log.debug("rank: ", score=score_and_assoc[0], weight=weights[idx], assoc=score_and_assoc[1])
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

    datasource_id = connections.db.datasource.find_first().id

    question = sys.argv[1]

    ranks = Ranker(connections.db, datasource_id).rank(question)
    print(ranks)
