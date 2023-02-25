"""
The datamodule wraps each dataset (train, test, validation) and provides a dataloader for each
"""

import pytorch_lightning as pl
from torch.utils.data import DataLoader

from python.ranker.ranker_dataset import RankerDataset


class RankerDataModule(pl.LightningDataModule):
    def __init__(self, dataset_element_type: str, batch_size: int = 32, num_workers: int = 0):
        # :param dataset_element_type: "table" | "column" | "value"
        super().__init__()

        self.batch_size = batch_size
        self.num_workers = num_workers

        device = "cpu"
        # device = "mps"

        self.train_dataset = RankerDataset(dataset_element_type, "train", device=device)
        self.test_dataset = RankerDataset(dataset_element_type, "test", device=device)
        self.val_dataset = RankerDataset(dataset_element_type, "validation", device=device)

    def train_dataloader(self):
        return DataLoader(self.train_dataset, batch_size=self.batch_size, num_workers=self.num_workers)

    def val_dataloader(self):
        return DataLoader(self.val_dataset, batch_size=self.batch_size, num_workers=self.num_workers)

    def test_dataloader(self):
        return DataLoader(self.test_dataset, batch_size=self.batch_size, num_workers=self.num_workers)


if __name__ == "__main__":
    dm = RankerDataModule("columns")

    print(len(dm.train_dataset))
    print(len(dm.test_dataset))
    print(len(dm.val_dataset))

    print(dm.train_dataset[0])
    print(dm.test_dataset[0])
    print(dm.val_dataset[0])

    for train_example in dm.train_dataloader():
        print(train_example)
