"""
Generate training data (from the local db) and train the Learned Ranker model
"""

# TODO should move to the cli interface

import shutil

from decouple import config

from python.ranker.column_ranker_model import ColumnRankerModel
from python.ranker.dataset_generator.dataset_generator import DatasetGenerator
from python.ranker.dataset_generator.utils import ranker_datasets_path
from python.ranker.table_ranker_model import TableRankerModel
from python.ranker.values_ranker_model import ValuesRankerModel

if not config("TRAIN_ONLY", default=False, cast=bool):
    # Clear previous dataset files
    shutil.rmtree(f"{ranker_datasets_path()}/ranker", ignore_errors=True)

    # Generate the training data
    # We need to split the evaluationQuestions into 3 groups, but based on the evaluationQuestionGroup.
    # The typical way to do this in ML is to just mod the id, since the assumption is you have a large eval set.
    # However, you do not want an even split. Usually you do about 70% in training and the rest in test and validation
    DatasetGenerator().run("train", 10, list(range(0, 7)))
    DatasetGenerator().run("test", 10, list(range(7, 8)))
    DatasetGenerator().run("validation", 10, list(range(8, 9)))

TableRankerModel.train_model()
ColumnRankerModel.train_model()
ValuesRankerModel.train_model()
