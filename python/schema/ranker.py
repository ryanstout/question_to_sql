from python.setup import log

import sys
import time
import typing as t

from decouple import config

from python.embeddings.ann_search import AnnSearch
from python.embeddings.embedding import generate_embedding
from python.embeddings.openai_embedder import OpenAIEmbedder
from python.utils.db import application_database_connection


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

        indexes_path = config("FAISS_INDEXES_PATH")

        # Load the faiss indexes
        self.idx_table_names = AnnSearch(0, f"{indexes_path}/{datasource_id}/table_names")
        self.idx_column_names = AnnSearch(1, f"{indexes_path}/{datasource_id}/column_names")
        self.idx_table_and_column_names = AnnSearch(3, f"{indexes_path}/{datasource_id}/table_and_column_names")

        # Table and Columns indexes
        # self.idx_table_and_column_names_and_values = AnnSearch(
        #     datasource_id, 4, f"{indexes_path}/{datasource_id}/table_and_column_names_and_values")
        self.idx_column_name_and_all_column_values = AnnSearch(
            5, f"{indexes_path}/{datasource_id}/column_name_and_all_column_values"
        )
        self.idx_table_column_and_value = AnnSearch(6, f"{indexes_path}/{datasource_id}/table_column_and_value")

        # Cell values
        self.idx_values = AnnSearch(2, f"{indexes_path}/{datasource_id}/values")

    def rank(
        self,
        query: str,
        embedder=OpenAIEmbedder,
        cache_results=True,
        table_weights=None,
        column_weights=None,
        value_weights=None,
    ) -> SCHEMA_RANKING_TYPE:
        # lists as defaults is dangerous, so we set defaults here
        # the array represents weights for 3 faiss indexes for each type
        if table_weights is None:
            table_weights = [0.3, 0.0, 0.1]
        if column_weights is None:
            column_weights = [0.1, 0.0, 0.0]
        if value_weights is None:
            value_weights = [0.5, 0.0]

        t1 = time.time()
        query_embedding = generate_embedding(query, embedder=embedder, cache_results=cache_results)

        log.debug("Start ranking")
        # Fetch ranked table id
        table_matches = self.idx_table_names.search(query_embedding, 1000)
        tables_with_columns_matches = self.idx_column_names.search(query_embedding, 1000)
        # log.debug("Table matches", matches=table_matches)

        columns_matches = self.idx_column_names.search(query_embedding, 10000)
        column_name_and_all_column_values_matches = self.idx_column_name_and_all_column_values.search(
            query_embedding, 1000
        )
        # log.debug("Column matches", matches=columns_matches)

        # search for value hint matches in the faaise index
        value_hint_search_limit = 50
        value_matches = self.idx_values.search(query_embedding, value_hint_search_limit)
        table_column_value_matches = self.idx_values.search(query_embedding, value_hint_search_limit)

        tables = self.merge_ranks([table_matches, tables_with_columns_matches, value_matches], table_weights, 0)
        columns = self.merge_ranks(
            [columns_matches, column_name_and_all_column_values_matches, value_matches], column_weights, 1
        )
        values = self.merge_ranks([value_matches, table_column_value_matches], value_weights, 2)

        # rankings = list(map(lambda x: ElementRank(table_id=x[1][0], column_id=x[1][1], value_hint=x[1][2], score=x[0]), tables + columns + values))
        rankings = list(
            map(
                lambda x: ElementRank(table_id=x[1][0], column_id=x[1][1], value_hint=x[1][2], score=x[0]),
                tables + columns + values,
            )
        )

        # Sort rankings by score
        rankings.sort(key=lambda x: x["score"], reverse=True)

        # for element_rank in rankings:
        #     log.debug("rank: ", score=element_rank["score"], assoc=[element_rank["table_id"], element_rank["column_id"], element_rank["value_hint"]])

        t2 = time.time()
        log.debug("Ranking fetch: ", time=t2 - t1)

        return rankings

    def merge_ranks(self, scores_and_associations, weights, remove_dups_idx=None):
        # Merge the output of multiple AnnSearch#search's via the passed in
        # weights
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
    db = application_database_connection()

    datasource_id = db.datasource.find_first()
    if datasource_id:
        datasource_id = datasource_id.id
    else:
        raise Exception("No datasource found")

    question = sys.argv[1]

    ranks = Ranker(db, datasource_id).rank(question)
    print(ranks)
