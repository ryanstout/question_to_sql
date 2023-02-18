"""
A dataset that pulls training examples from the evaluationQuestion and evaluationQuestionGroup tables.

We split on the question group not the individual question to prevent leakage between train and test.

Takes in a set id and number of sets and splits using a mod on the id
"""

from typing import Tuple

from torch.utils.data import Dataset

from python import utils

db = utils.db.application_database_connection()


class RankerDataset(Dataset):
    set_indexes: range
    mod_by: int

    def __init__(self, set_indexes: range, mod_by: int):
        self.set_indexes = set_indexes
        self.mod_by = mod_by

        set_indexes_in_clause = ",".join([str(idx) for idx in set_indexes])
        question_group_ids = db.query_raw(
            f'SELECT id FROM "EvaluationQuestionGroup" WHERE (id % {mod_by}) IN ({set_indexes_in_clause});'
        )

        self.ids = []
        # pylint can't detect question_group_ids is iterable: https://github.com/PyCQA/pylint/issues/3105
        for question_group in question_group_ids:  # pylint: disable=not-an-iterable
            # Select the id's of each child question
            # Can't select yet: https://github.com/RobertCraigie/prisma-client-py/issues/19
            questions = db.evaluationquestion.find_many(where={"evaluationQuestionGroupId": question_group["id"]})
            for question in questions:
                self.ids.append(question.id)

    def __getitem__(self, index) -> Tuple[str, str]:
        print("GET INDEX: ", index, len(self.ids))
        question = db.evaluationquestion.find_first(
            where={"id": self.ids[index]}, include={"evaluationQuestionGroup": True}
        )

        if question is None:
            raise ValueError(f"Question with id {self.ids[index]} not found")

        if question.evaluationQuestionGroup is None:
            raise ValueError(f"Question group for question {self.ids[index]} not found")

        x = question.question
        y = question.evaluationQuestionGroup.correctSql

        if y is None:
            raise ValueError(f"Correct SQL for question group {question.evaluationQuestionGroup.id} not found")

        print(x, y)

        return x, y

    def __len__(self) -> int:
        return len(self.ids)
