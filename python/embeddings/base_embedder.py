import numpy as np
from torch import Tensor


class BaseEmbedder:
    def encode(self, content_str: str) -> np.ndarray:
        raise NotImplementedError("embed not implemented")
