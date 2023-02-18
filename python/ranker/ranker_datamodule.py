import pytorch_lightning as pl

from python.ranker.ranker_dataset import RankerDataset


class RankerDataModule(pl.LightningDataModule):
    def __init__(self):
        super().__init__()
        self.train_dataset = RankerDataset(range(0, 8), 10)  # 70%
        self.test_dataset = RankerDataset(range(8, 9), 3)  # 15%
        self.val_dataset = RankerDataset(range(9, 10), 3)  # 15%


if __name__ == "__main__":
    dm = RankerDataModule()

    print(len(dm.train_dataset))
    print(len(dm.test_dataset))
    print(len(dm.val_dataset))

    print(dm.train_dataset[0])
    print(dm.test_dataset[0])
    print(dm.val_dataset[0])
