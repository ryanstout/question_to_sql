import pytorch_lightning as pl
import torch
import torch.backends.mps
from decouple import config
from torch import nn
from torch.nn import functional as F

from python.ranker.dataset_generator.utils import ranker_models_path
from python.ranker.ranker_datamodule import RankerDataModule
from python.utils.torch import device_type


class ColumnRankerModel(pl.LightningModule):
    def __init__(self):
        super().__init__()
        # self.model = nn.Sequential(nn.Linear(7, 50), nn.ReLU(), nn.Linear(50, 1))
        self.model = nn.Sequential(nn.Linear(7, 50), nn.ReLU(), nn.Linear(50, 1))

        # self.model = nn.Sequential(
        #     nn.Linear(7, 15),
        #     nn.ReLU(),
        #     nn.BatchNorm1d(15),
        #     nn.Linear(15, 5),
        #     nn.ReLU(),
        #     nn.BatchNorm1d(5),
        #     nn.Linear(5, 1),
        # )

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
        ranker_data = RankerDataModule("columns", batch_size=256)

        model = ColumnRankerModel()
        model.to(device_type())

        # training
        trainer = pl.Trainer(
            default_root_dir=f"{ranker_models_path()}/column_ranker", max_epochs=1000
        )  # gpus=4, num_nodes=8, precision=16, limit_train_batches=0.5)
        trainer.fit(model, datamodule=ranker_data)

        trainer.test(model, datamodule=ranker_data)
        trainer.validate(model, datamodule=ranker_data)


if __name__ == "__main__":
    ColumnRankerModel.train_model()
