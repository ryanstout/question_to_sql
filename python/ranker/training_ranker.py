from dataclasses import dataclass, field
from typing import TypedDict

from decouple import config

from python.embeddings.ann_search import AnnSearch
from python.embeddings.embedding import generate_embedding
from python.embeddings.openai_embedder import OpenAIEmbedder
from python.sql.types import DbElement, DbElementIds, ElementScores


class TrainingRanker:
    rankings: dict[DbElementIds, ElementScores]

    def __init__(self, datasource_id: int):

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

    def rank(self, query: str, embedder=OpenAIEmbedder, cache_results=True) -> dict[DbElementIds, ElementScores]:
        query_embedding = generate_embedding(query, embedder=embedder, cache_results=cache_results)

        self.rankings = {}

        idx_table_names_rankings = self.idx_table_names.search(query_embedding, 1000)
        idx_column_names_rankings = self.idx_column_names.search(query_embedding, 1000)
        idx_table_and_column_names_rankings = self.idx_table_and_column_names.search(query_embedding, 1000)
        idx_column_name_and_all_column_values_rankings = self.idx_column_name_and_all_column_values.search(
            query_embedding, 1000
        )
        idx_table_column_and_value_rankings = self.idx_table_column_and_value.search(query_embedding, 1000)
        idx_values_rankings = self.idx_values.search(query_embedding, 1000)

        self.merge_search_results(idx_table_names_rankings, "table_names")
        self.merge_search_results(idx_column_names_rankings, "column_names")
        self.merge_search_results(idx_table_and_column_names_rankings, "table_and_column_names")
        self.merge_search_results(idx_column_name_and_all_column_values_rankings, "column_name_and_all_column_values")
        self.merge_search_results(idx_table_column_and_value_rankings, "table_column_and_value")
        self.merge_search_results(idx_values_rankings, "values")

        return self.rankings

    def merge_search_results(self, results: list[tuple[float, DbElementIds]], ranking_name: str):
        for ranking in results:
            score, db_element = ranking

            if db_element not in self.rankings:
                self.rankings[db_element] = ElementScores()

            # Update the score on the ElementRanking
            setattr(self.rankings[db_element], ranking_name + "_score", score)


if __name__ == "__main__":
    from pprint import pprint

    ranker = TrainingRanker(1)

    rank_results = ranker.rank("How many orders from Montana?")
    pprint(rank_results)
