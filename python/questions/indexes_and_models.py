"""
The Ranker, LearnedRanker, and FewShotEmbeddings all should be loaded into ram once, then queried. This class acts as
a singleton, then allows retrieving the correct instance.
"""

from decouple import config

from python.prompts.few_shot_embeddings.search import FewShotEmbeddingSearch
from python.schema.learned_ranker import LearnedRanker
from python.schema.ranker import Ranker
from python.utils.db import application_database_connection

from prisma import Prisma

db = application_database_connection()


class IndexesAndModels:
    def __init__(self):
        self.use_learned_ranker = config("ENABLE_LEARNED_RANKER", default=True, cast=bool)
        self.few_shot_path = config("FEW_SHOT_EMBEDDINGS_PATH")

        self.rankers = {}
        self.few_shot_embeddings = {}

    def ranker(self, data_source_id: int) -> Ranker:
        # Lazy load ranker
        if data_source_id not in self.rankers:
            if self.use_learned_ranker:
                self.rankers[data_source_id] = LearnedRanker(data_source_id)
            else:
                self.rankers[data_source_id] = Ranker(data_source_id)

        return self.rankers[data_source_id]

    def few_shot(self, data_source_id: int) -> FewShotEmbeddingSearch:
        # Lazy load few shot embeddings
        if data_source_id not in self.few_shot_embeddings:
            self.few_shot_embeddings[data_source_id] = FewShotEmbeddingSearch(
                data_source_id, f"{self.few_shot_path}/{data_source_id}"
            )

        return self.few_shot_embeddings[data_source_id]
