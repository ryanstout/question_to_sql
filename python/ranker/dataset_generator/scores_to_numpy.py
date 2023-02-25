"""
The way we go from an ElementScores object to a numpy array for training varies depending on the type of DbElementId
we are working with. This file pulls out that logic.
"""

import numpy as np

from python.sql.types import ElementScores


def table_scores_to_numpy(table_scores: list[ElementScores]) -> np.ndarray:
    x = np.empty((len(table_scores), 3), dtype=np.float32)

    for idx, table_score in enumerate(table_scores):
        # Create the input weights
        x[idx, 0] = table_score.table_name_score or 0
        x[idx, 1] = table_score.table_and_all_column_names_score or 0
        x[idx, 2] = table_score.table_and_all_column_names_and_all_values_score or 0
        # x[idx, 3] = element_scores.column_name_score or 0
        # x[idx, 4] = element_scores.table_and_column_name_score or 0
        # x[idx, 5] = element_scores.column_name_and_all_values_score or 0
        # x[idx, 6] = element_scores.table_and_column_name_and_all_values_score or 0
        # x[idx, 7] = element_scores.value_score or 0
        # x[idx, 8] = element_scores.table_column_and_value_score or 0

        # x[idx, 8] = element_scores.table_table_and_value_score or 0

    return x


def column_scores_to_numpy(column_scores: list[ElementScores]) -> np.ndarray:
    x = np.empty((len(column_scores), 7), dtype=np.float32)

    for idx, column_score in enumerate(column_scores):
        # Create the input weights
        x[idx, 0] = column_score.table_name_score or 0
        x[idx, 1] = column_score.table_and_all_column_names_score or 0
        x[idx, 2] = column_score.table_and_all_column_names_and_all_values_score or 0
        x[idx, 3] = column_score.column_name_score or 0
        x[idx, 4] = column_score.table_and_column_name_score or 0
        x[idx, 5] = column_score.column_name_and_all_values_score or 0
        x[idx, 6] = column_score.table_and_column_name_and_all_values_score or 0
        # x[idx, 7] = column_score.value_score or 0
        # x[idx, 8] = column_score.table_column_and_value_score or 0

    return x


def values_scores_to_numpy(values_scores: list[ElementScores]) -> np.ndarray:
    x = np.empty((len(values_scores), 2), dtype=np.float32)

    for idx, value_score in enumerate(values_scores):
        # Feed in only these two for values for now
        x[idx, 0] = value_score.value_score or 0
        x[idx, 1] = value_score.table_column_and_value_score or 0

    return x
