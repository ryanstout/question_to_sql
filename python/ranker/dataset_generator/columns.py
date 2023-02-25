import os
from random import sample

import numpy as np

from python.ranker.dataset_generator.scores_to_numpy import column_scores_to_numpy

np.set_printoptions(edgeitems=10, linewidth=180)

from python.sql.types import DbElementIds, ElementScores


def create_column_training_examples(
    dataset_name: str,
    question_id: int,
    column_rankings: dict[DbElementIds, ElementScores],
    column_touch_point_ids: dict[DbElementIds, int],
):
    column_scores: list[ElementScores] = []

    xs = []
    ys = []

    # Create positive and negative examples for values
    for db_element in column_touch_point_ids.keys():
        element_scores = column_rankings[db_element]
        del column_rankings[db_element]  # pull all positives so we can just sample negatives
        # log.debug("POS: ", convert_db_element_ids_to_db_element(db_element))
        column_scores.append(element_scores)
        ys.append(1)

    xs.append(column_scores_to_numpy(column_scores))
    column_scores = []

    # Create negative examples by grabbing random DbElements from the remaining rankings
    negative_element_sub_sample = sample(list(column_rankings.keys()), len(column_touch_point_ids))
    for db_element in negative_element_sub_sample:
        # log.debug("NEG: ", convert_db_element_ids_to_db_element(db_element))
        element_scores = column_rankings[db_element]
        column_scores.append(element_scores)
        ys.append(0)

    xs.append(column_scores_to_numpy(column_scores))

    x = np.concatenate(xs, axis=0)
    y = np.array(ys, dtype=np.float32)

    y_exp = np.expand_dims(y, axis=1)
    print(x.shape, y_exp.shape)
    print(np.concatenate((x, y_exp), axis=1))

    if x.shape[0] > 0:
        os.makedirs("tmp/datasets/ranker/columns", exist_ok=True)
        np.savez_compressed(f"tmp/datasets/ranker/columns/{dataset_name}_{question_id}.npz", x=x, y=y)
