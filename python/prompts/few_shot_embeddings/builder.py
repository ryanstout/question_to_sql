"""
Each data source gets its own few shot embedding index, which indexes each evaluation question so we can match
to the users question when generating prompts.
"""

from python.embeddings.ann_index import AnnIndex
from python.utils.db import application_database_connection

from prisma.enums import EvaluationStatus

db = application_database_connection()


class FewShotEmbeddingsBuilder:
    def __init__(self, data_source_id: int, path: str):
        self.path = path
        self.index = AnnIndex(path)

        # Index each evaluation question
        for question_group in db.evaluationquestiongroup.find_many(
            where={"dataSourceId": data_source_id, "status": EvaluationStatus.CORRECT},
            include={"evaluationQuestions": True},
        ):
            questions = question_group.evaluationQuestions
            if questions:
                for question in questions:
                    self.index.add(question.question, question.id, None, None)

        self.index.save()


if __name__ == "__main__":
    from decouple import config

    from python.utils.logging import log

    few_shot_path = config("FEW_SHOT_EMBEDDINGS_PATH")

    log.info("Building few shot embeddings")
    for data_source in db.datasource.find_many():
        log.info("Building few shot embeddings for data source", data_source=data_source.id)
        FewShotEmbeddingsBuilder(data_source.id, f"{few_shot_path}/{data_source.id}")
        log.info("Done")
