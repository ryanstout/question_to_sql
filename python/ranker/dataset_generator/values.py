import os
from random import sample

import numpy as np

from python.ranker.dataset_generator.scores_to_numpy import values_scores_to_numpy
from python.ranker.dataset_generator.utils import ranker_datasets_path
from python.ranker.types import DatasetPartitionType
from python.sql.types import DbElementIds, ElementScores
from python.utils.logging import log


def find_matching_db_element_case_insensitive(
    value_rankings: dict[DbElementIds, ElementScores], db_element: DbElementIds
) -> DbElementIds:
    """
    Because equals comparisons in snowflake are case sensitive, we have openai generate LOWER(column) = {lower str}

    This means if we can't find a direct match, we should fall back to a case insensitive value match
    """
    if db_element not in value_rankings:
        # Try a case insensitive match
        if db_element.value is not None:

            # TODO: This is going to be slow, optimize later
            for db_el_match in value_rankings.keys():
                if (
                    db_el_match.value
                    and db_element.table == db_el_match.table
                    and db_element.column == db_el_match.column
                ):
                    if db_element.value.lower() == db_el_match.value.lower():
                        # Update the match to be the DbElement key with the correct case
                        db_element = db_el_match
                        break
    return db_element


def create_value_training_examples(
    dataset_name: DatasetPartitionType,
    question_id: int,
    value_rankings: dict[DbElementIds, ElementScores],
    # touch points are only outputted on =, not likes
    value_touch_point_ids: dict[DbElementIds, int],
):
    values_scores: list[ElementScores] = []

    xs = []
    ys = []

    # Create positive and negative examples for values
    for db_element in value_touch_point_ids.keys():
        # Grab ElementScores for the touch point

        # Do a case sensitive lookup if needed
        db_element = find_matching_db_element_case_insensitive(value_rankings, db_element)

        if db_element not in value_rankings:
            log.error("touch point not found", db_element=db_element)
        else:
            log.debug("touch point found", db_element=db_element)
            element_scores = value_rankings[db_element]
            del value_rankings[db_element]
            values_scores.append(element_scores)
            ys.append(1)

    xs.append(values_scores_to_numpy(values_scores))
    values_scores = []

    # Create negative examples by grabbing random DbElements from the remaining rankings
    negative_element_sub_sample = sample(list(value_rankings.keys()), len(value_touch_point_ids))
    for db_element in negative_element_sub_sample:
        element_scores = value_rankings[db_element]
        values_scores.append(element_scores)
        ys.append(0)

    xs.append(values_scores_to_numpy(values_scores))

    x = np.concatenate(xs, axis=0)
    y = np.array(ys, dtype=np.float32)

    if x.shape[0] > 0:
        os.makedirs(f"{ranker_datasets_path()}/ranker/values", exist_ok=True)
        np.savez_compressed(f"{ranker_datasets_path()}/ranker/values/{dataset_name}_{question_id}.npz", x=x, y=y)
