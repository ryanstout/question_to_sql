"""
A dataset that pulls training examples from the evaluationQuestion and evaluationQuestionGroup tables.

We split on the question group not the individual question to prevent leakage between train and test.

Takes in a set id and number of sets and splits using a mod on the id
"""

import glob

import numpy as np
import torch
from torch.utils.data import Dataset

from python.ranker.dataset_generator.utils import ranker_datasets_path
from python.ranker.types import DatasetElementType, DatasetPartitionType
from python.utils.logging import log
from python.utils.torch import device_type


class RankerDataset(Dataset):
    def __init__(
        self,
        dataset_element_type: DatasetElementType,
        dataset_partition: DatasetPartitionType,
    ):
        # Currently we can fit all training in ram, so bring it into a single numpy array
        numpy_files = glob.glob(f"{ranker_datasets_path()}/ranker/{dataset_element_type}/{dataset_partition}_*.npz")

        log.info(
            "loading numpy files", files=numpy_files, element_type=dataset_element_type, partition=dataset_partition
        )

        # The standard x (features) and y (target values) in ML for a dataset:
        # https://enjoymachinelearning.com/blog/x-and-y-in-machine-learning/
        xs = []
        ys = []

        for numpy_file in numpy_files:
            data = np.load(numpy_file)
            xs.append(data["x"])
            ys.append(data["y"])

        if not xs or not ys:
            raise ValueError(
                f"not enough training data for {dataset_element_type}.{dataset_partition}, add more evaluation questions"
            )

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
