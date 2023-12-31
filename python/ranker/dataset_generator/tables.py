import os
from random import sample

import numpy as np

from python.ranker.dataset_generator.scores_to_numpy import table_scores_to_numpy
from python.ranker.dataset_generator.utils import ranker_datasets_path
from python.ranker.types import DatasetPartitionType
from python.sql.types import DbElementIds, ElementScores

# TODO we should make sure there are no import side effects
# TODO also, is this just debug/development config or does it have any production use?
np.set_printoptions(edgeitems=10, linewidth=180)


def create_table_training_examples(
    dataset_name: DatasetPartitionType,
    question_id: int,
    table_rankings: dict[DbElementIds, ElementScores],
    table_touch_point_ids: dict[DbElementIds, int],
):
    table_scores: list[ElementScores] = []

    xs = []
    ys = []

    # Create positive and negative examples for values
    for db_element in table_touch_point_ids.keys():
        element_scores = table_rankings[db_element]
        del table_rankings[db_element]  # pull all positives so we can just sample negatives
        # log.debug("POS: ", convert_db_element_ids_to_db_element(db_element))
        table_scores.append(element_scores)
        ys.append(1)

    xs.append(table_scores_to_numpy(table_scores))
    table_scores = []

    # Create negative examples by grabbing random DbElements from the remaining rankings
    negative_element_sub_sample = sample(list(table_rankings.keys()), len(table_touch_point_ids))
    for db_element in negative_element_sub_sample:
        # log.debug("NEG: ", convert_db_element_ids_to_db_element(db_element))
        element_scores = table_rankings[db_element]
        table_scores.append(element_scores)
        ys.append(0)

    xs.append(table_scores_to_numpy(table_scores))

    x = np.concatenate(xs, axis=0)
    y = np.array(ys, dtype=np.float32)

    # y_exp = np.expand_dims(y, axis=1)
    # print(np.concatenate((x, y_exp), axis=1))

    if x.shape[0] > 0:
        os.makedirs(f"{ranker_datasets_path()}/ranker/tables", exist_ok=True)
        np.savez_compressed(f"{ranker_datasets_path()}/ranker/tables/{dataset_name}_{question_id}.npz", x=x, y=y)
