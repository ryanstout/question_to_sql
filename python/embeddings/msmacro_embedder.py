import numpy as np
import torch
from sentence_transformers import SentenceTransformer, util
from torch import Tensor

from python.utils.torch import device_type


class MSMarcoEmbedder:
    def __init__(self):
        self.model = SentenceTransformer(
            # 'msmarco-distilbert-base-v4',
            # 'all-MiniLM-L6-v2',
            "all-mpnet-base-v2",  # dot-score, Large model, good for semantic search
            # 'msmarco-distilbert-base-tas-b', # dot product
            device=device_type(),
        )  # use cosine

    def encode(self, content: str) -> np.ndarray:
        result = self.model.encode(content)
        if isinstance(result, Tensor):
            # Force to tensor
            result = result.numpy()
        elif isinstance(result, list):
            raise ValueError("Expected a single embedding, got a list")

        return result

    def test(self):
        # t1 = time.time()
        # for i in range(100):
        #     a1 = self.model.encode([
        #         'How many orders are there from Montana?',
        #         'When was the first order placed?',
        #     ], device=device, batch_size=50)
        # t2 = time.time()
        # print(a1.shape, t2-t1)
        a2 = self.encode("Nevada, Illinois, California, Texas, Florida")
        a3 = self.encode("Milk, Yogurt, Eggs, Cheese, Ham, More, Things, To, Fill, Up, List")
        a4 = self.encode("STATE: Montana")

        e1 = self.encode("How many orders are there from Montana?")

        print("Similarity:", self.np_dot_score(e1, a2))
        print("Similarity:", self.np_dot_score(e1, a3))
        print("Similarity:", self.np_dot_score(e1, a4))

        # print("Similarity:", util.cos_sim(query_embedding, a1))
        # print("Similarity:", util.cos_sim(e1, a2))
        # print("Similarity:", util.cos_sim(e1, a3))
        # print("Similarity:", util.cos_sim(e1, a4))

    def np_dot_score(self, a: np.ndarray, b: np.ndarray) -> Tensor:
        return util.dot_score(torch.from_numpy(a), torch.from_numpy(b))


if __name__ == "__main__":
    MSMarcoEmbedder().test()
