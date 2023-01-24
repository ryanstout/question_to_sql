from sentence_transformers import SentenceTransformer, util
import time
import torch


class MSMarcoEmbeddings:
    def __init__(self):
        device = "cpu"
        # device = 'mps'  # Move to M1 Mac GPU

        self.model = SentenceTransformer(
            # 'msmarco-distilbert-base-v4',
            # 'all-MiniLM-L6-v2',
            "all-mpnet-base-v2",  # dot-score, Large model, good for semantic search
            # 'msmarco-distilbert-base-tas-b', # dot product
            device=device,
        )  # use cosine

    def encode(self, content: str):
        return self.model.encode(content)

    def test(self):
        # t1 = time.time()
        # for i in range(100):
        #     a1 = self.model.encode([
        #         'How many orders are there from Montana?',
        #         'When was the first order placed?',
        #     ], device=device, batch_size=50)
        # t2 = time.time()
        # print(a1.shape, t2-t1)
        a2 = self.model.encode("Nevada, Illinois, California, Texas, Florida")
        a3 = self.model.encode("Milk, Yogurt, Eggs, Cheese, Ham, More, Things, To, Fill, Up, List")
        a4 = self.model.encode("STATE: Montana")

        e1 = self.model.encode("How many orders are there from Montana?")

        print("Similarity:", util.dot_score(e1, a2))
        print("Similarity:", util.dot_score(e1, a3))
        print("Similarity:", util.dot_score(e1, a4))

        # print("Similarity:", util.cos_sim(query_embedding, a1))
        # print("Similarity:", util.cos_sim(e1, a2))
        # print("Similarity:", util.cos_sim(e1, a3))
        # print("Similarity:", util.cos_sim(e1, a4))


if __name__ == "__main__":
    MSMarcoEmbeddings().test()
