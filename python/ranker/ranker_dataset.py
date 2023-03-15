"""
A dataset that pulls training examples from the evaluationQuestion and evaluationQuestionGroup tables.

We split on the question group not the individual question to prevent leakage between train and test.

Takes in a set id and number of sets and splits using a mod on the id
"""

import glob

import numpy as np
import torch
from decouple import config
from torch.utils.data import Dataset

from python import utils
from python.ranker.types import DatasetElementType, DatasetPartitionType
from python.utils.torch import device_type

db = utils.db.application_database_connection()


datasets_path = config("DATASETS_PATH")


class RankerDataset(Dataset):
    def __init__(
        self,
        dataset_element_type: DatasetElementType,
        dataset_partition: DatasetPartitionType,
    ):
        # Currently we can fit all training in ram, so bring it into a single numpy array
        numpy_files = glob.glob(f"{datasets_path}/ranker/{dataset_element_type}/{dataset_partition}_*.npz")

        # TODO what are these for?
        xs = []
        ys = []

        for numpy_file in numpy_files:
            data = np.load(numpy_file)
            # TODO what are x & y in these files?
            xs.append(data["x"])
            ys.append(data["y"])

        if not xs or not ys:
            raise ValueError("not enough training data, add more evaluation questions")

        self.xs = torch.from_numpy(np.concatenate(xs, axis=0))
        self.ys = torch.from_numpy(np.concatenate(ys, axis=0))

        self.xs.to(device_type())
        self.ys.to(device_type())

    def __getitem__(self, index):
        x = self.xs[index, :]
        y = self.ys[index]

        if torch.isnan(x).any() or np.isnan(y).any():
            raise ValueError(f"Found nan in x: {x} or y: {y}")

        return x, y

    def __len__(self) -> int:
        return self.xs.shape[0]
