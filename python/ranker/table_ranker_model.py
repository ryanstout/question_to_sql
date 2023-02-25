import pytorch_lightning as pl
import torch
from torch import nn
from torch.nn import functional as F

from python.ranker.ranker_datamodule import RankerDataModule


class TableRankerModel(pl.LightningModule):
    def __init__(self):
        super().__init__()
        self.model = nn.Sequential(nn.Linear(3, 50), nn.ReLU(), nn.Linear(50, 1))

    def forward(self, x):
        y_hat = self.model(x)[:, 0]
        return y_hat

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
        return optimizer

    def training_step(self, train_batch, _batch_idx):
        x, y = train_batch
        y_hat = self.forward(x)
        loss = F.mse_loss(y_hat, y)
        self.log("train_loss", loss)
        return loss

    def test_step(self, test_batch, _batch_idx):
        x, y = test_batch
        y_hat = self.forward(x)
        loss = F.mse_loss(y_hat, y)
        self.log("test_loss", loss)
        return loss

    def validation_step(self, val_batch, _batch_idx):
        x, y = val_batch
        y_hat = self.forward(x)
        loss = F.mse_loss(y_hat, y)
        self.log("val_loss", loss)

    @classmethod
    def train_model(cls):
        ranker_data = RankerDataModule("tables", batch_size=256)

        # model
        model = TableRankerModel()

        # training
        trainer = pl.Trainer(
            default_root_dir="tmp/models/table_ranker"
        )  # gpus=4, num_nodes=8, precision=16, limit_train_batches=0.5)
        trainer.fit(model, datamodule=ranker_data)

        trainer.test(model, datamodule=ranker_data)
        trainer.validate(model, datamodule=ranker_data)


if __name__ == "__main__":
    TableRankerModel.train_model()
