import os
from pprint import pprint
from random import sample
from typing import List, Tuple, TypeAlias

import numpy as np

from python.ranker.training_ranker import TrainingRanker
from python.sql.types import DbElement, DbElementIds, ElementScores
from python.sql.utils.touch_points import get_touch_points_ids
from python.utils.batteries import not_none
from python.utils.db import application_database_connection

from prisma.enums import EvaluationStatus
from prisma.models import EvaluationQuestion, EvaluationQuestionGroup

db = application_database_connection()


ElementTrainingExamples: TypeAlias = list[Tuple[DbElementIds, ElementScores, int]]


class RankerDatasetGenerator:
    rankings: dict[DbElementIds, ElementScores]
    touch_points: list[DbElementIds]

    def run(self, dataset_name: str, mod_by: int, set_indexes: List[int]):
        self.dataset_name = dataset_name
        set_indexes_in_clause = ",".join([str(idx) for idx in set_indexes])

        question_groups = db.evaluationquestiongroup.query_raw(
            f'SELECT * FROM "EvaluationQuestionGroup" WHERE (id % {mod_by}) IN ({set_indexes_in_clause});'
        )

        for question_group in question_groups:
            self.process_question_group(question_group)

    def process_question_group(self, question_group: EvaluationQuestionGroup):
        question_groups = db.evaluationquestiongroup.find_many(
            where={"status": EvaluationStatus.CORRECT}, include={"evaluationQuestions": True, "dataSource": True}
        )
        for question_group in question_groups:
            questions = question_group.evaluationQuestions
            if questions:
                for question in questions:
                    self.process_question(question_group, question)

    def process_question(self, question_group: EvaluationQuestionGroup, question: EvaluationQuestion):
        self.rankings = TrainingRanker(question_group.dataSourceId).rank(question.question)

        # Split rankings out for each table, column, and value
        table_scores: dict[DbElementIds, ElementScores] = {}
        column_scores: dict[DbElementIds, ElementScores] = {}
        value_scores: dict[DbElementIds, ElementScores] = {}

        for db_element, element_scores in self.rankings.items():
            if db_element.value is not None:
                value_scores[db_element] = element_scores
            elif db_element.column is not None:
                column_scores[db_element] = element_scores
            else:
                table_scores[db_element] = element_scores

        # Get the touch points for the correct sql
        self.touch_points = get_touch_points_ids(not_none(question_group.correctSql), question_group.dataSourceId)

        # Split touch points out for each table, column, and value
        table_touch_points: dict[DbElementIds, int] = {}
        column_touch_points: dict[DbElementIds, int] = {}
        value_touch_points: dict[DbElementIds, int] = {}

        for touch_point in self.touch_points:
            _, column_name, column_value_name = touch_point

            if column_value_name is not None:
                value_touch_points[touch_point] = 1
            elif column_name is not None:
                column_touch_points[touch_point] = 1
            else:
                table_touch_points[touch_point] = 1

        self.create_value_training_examples(value_scores, value_touch_points)

    def create_value_training_examples(
        self, value_rankings: dict[DbElementIds, ElementScores], value_touch_point_ids: dict[DbElementIds, int]
    ):
        values_dataset: ElementTrainingExamples = []

        print("Touch Points", value_touch_point_ids)

        # Create positive and negative examples for values
        for db_element in value_touch_point_ids.keys():
            # Grab ElementScores for the touch point
            element_scores = value_rankings[db_element]
            del value_rankings[db_element]
            values_dataset.append((db_element, element_scores, 1))

        # Create negative examples by grabbing random DbElements from the remaining rankings
        negative_element_sub_sample = sample(list(value_rankings.keys()), len(value_touch_point_ids))
        for db_element in negative_element_sub_sample:
            element_scores = value_rankings[db_element]
            values_dataset.append((db_element, element_scores, 0))

        x = np.empty((len(values_dataset), 2), dtype=np.float32)
        y = np.empty((len(values_dataset)), dtype=np.float32)

        # Write out the training examples for the values dataset
        for idx, (_, element_scores, pos_or_neg) in enumerate(values_dataset):
            # Create the input weights
            x[idx, 0] = element_scores.table_column_and_value_score or 0
            x[idx, 1] = element_scores.values_score or 0
            y[idx] = pos_or_neg

        os.makedirs("tmp/datasets/ranker", exist_ok=True)
        np.savez_compressed(f"tmp/datasets/ranker/{self.dataset_name}_values.npz", x=x, y=y)


if __name__ == "__main__":
    RankerDatasetGenerator().run("train", 10, list(range(0, 7)))

    # RankerDatasetGenerator().run("test", 10, list(range(7, 8)))
    # RankerDatasetGenerator().run("validation", 10, list(range(8, 9)))
