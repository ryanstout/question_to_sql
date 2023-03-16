"""
Dataset generation happens offline before the training starts. The resulting datasets for table, column, and values
are written to tmp/datasets/ranker

The train, test, validation split happens at the EvaluationQuestionGroup level so similar questions (and the same
correctSql don't overlap)
"""

import os
from typing import List

from python.ranker.dataset_generator.columns import create_column_training_examples
from python.ranker.dataset_generator.tables import create_table_training_examples
from python.ranker.dataset_generator.utils import ranker_datasets_path
from python.ranker.dataset_generator.values import create_value_training_examples
from python.ranker.training_ranker import TrainingRanker
from python.ranker.types import DatasetPartitionType
from python.sql.types import DbElementIds, ElementIdsAndScores, ElementScores
from python.sql.utils.touch_points import get_touch_points_ids
from python.utils.batteries import not_none
from python.utils.db import application_database_connection
from python.utils.logging import log

from prisma.models import EvaluationQuestion, EvaluationQuestionGroup

db = application_database_connection()


class DatasetGenerator:
    rankings: dict[DbElementIds, ElementScores]
    touch_points: list[DbElementIds]
    dataset_name: DatasetPartitionType

    # :param dataset_name: The name of the dataset to write to (e.g. "train", "test", "validation")
    # :param mod_by: The mod by value to use to split the dataset
    # :param set_indexes: When any index matches the mod, we include it in this dataset split
    def run(self, dataset_name: DatasetPartitionType, mod_by: int, set_indexes: List[int]):
        # TODO why is this call happening here? unrelated?
        os.makedirs(f"{ranker_datasets_path()}/ranker", exist_ok=True)

        self.dataset_name = dataset_name
        set_indexes_in_clause = ",".join([str(idx) for idx in set_indexes])

        question_groups = db.evaluationquestiongroup.query_raw(
            f"SELECT * FROM \"EvaluationQuestionGroup\" WHERE (id % {mod_by}) IN ({set_indexes_in_clause}) AND status='CORRECT';"
        )

        if len(question_groups) == 0:
            raise ValueError(f"No question groups found for dataset generation {set_indexes}")

        for question_group in question_groups:
            self.process_question_group(question_group)

    def process_question_group(self, question_group: EvaluationQuestionGroup):
        questions = db.evaluationquestion.find_many(where={"evaluationQuestionGroupId": question_group.id})
        if questions:
            for question in questions:
                self.process_question(question_group, question)

    def process_question(self, question_group: EvaluationQuestionGroup, question: EvaluationQuestion):
        log.info("process question", id=question.id, question=question.question)
        rankings = TrainingRanker(question_group.dataSourceId).rank(question.question)

        # Split rankings out for each table, column, and value
        table_scores: ElementIdsAndScores = rankings[0]
        column_scores: ElementIdsAndScores = rankings[1]
        value_scores: ElementIdsAndScores = rankings[2]

        # Get the touch points for the correct sql
        self.touch_points = get_touch_points_ids(not_none(question_group.correctSql), question_group.dataSourceId)

        # Split touch points out for each table, column, and value
        table_touch_point_ids: dict[DbElementIds, int] = {}
        column_touch_point_ids: dict[DbElementIds, int] = {}
        value_touch_point_ids: dict[DbElementIds, int] = {}

        for touch_point in self.touch_points:
            _, column_name, column_value_name = touch_point

            if column_value_name is not None:
                value_touch_point_ids[touch_point] = 1
            elif column_name is not None:
                column_touch_point_ids[touch_point] = 1
            else:
                table_touch_point_ids[touch_point] = 1

        create_table_training_examples(self.dataset_name, question.id, table_scores, table_touch_point_ids)
        create_column_training_examples(self.dataset_name, question.id, column_scores, column_touch_point_ids)
        create_value_training_examples(self.dataset_name, question.id, value_scores, value_touch_point_ids)
