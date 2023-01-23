from sentence_transformers import SentenceTransformer, util
import time
import torch


class MSMarcoEmbeddings:
    def __init__(self):
        self.model = SentenceTransformer(
            'msmarco-distilbert-base-v4')  # use cosine
        # model = SentenceTransformer('msmarco-distilbert-base-tas-b') # use dot product

        # Move to M1 Mac GPU
        # self.model.to(torch.device('mps'))
        # query_embedding = model.encode(
        #     'How many orders are there from Montana')
        t1 = time.time()
        for i in range(100):
            a1 = self.model.encode([
                'Alabama',
                'Alaska',
                'Arizona',
                'Arkansas',
                'California',
                'Colorado',
                'Connecticut',
                'Delaware',
                'Florida',
                'Georgia',
                'Hawaii',
                'Idaho',
                'IllinoisIndiana',
                'Iowa',
                'Kansas',
                'Kentucky',
                'Louisiana',
                'Maine',
                'Maryland',
                'Massachusetts',
                'Michigan',
                'Minnesota',
                'Mississippi',
                'Missouri',
                'MontanaNebraska',
                'Nevada',
                'New Hampshire',
                'New Jersey',
                'New Mexico',
                'New York',
                'North Carolina',
                'North Dakota',
                'Ohio',
                'Oklahoma',
                'Oregon',
                'PennsylvaniaRhode Island',
                'South Carolina',
                'South Dakota',
                'Tennessee',
                'Texas',
                'Utah',
                'Vermont',
                'Virginia',
                'Washington',
                'West Virginia',
                'Wisconsin',
                'Wyoming'
            ])
        t2 = time.time()
        print(a1.shape, t2-t1)
        # a2 = model.encode('STATE Nevada')
        # a3 = model.encode('A blog title')
        # a4 = model.encode('create table Order')

        # print("Similarity:", util.cos_sim(query_embedding, a1))
        # print("Similarity:", util.cos_sim(query_embedding, a2))
        # print("Similarity:", util.cos_sim(query_embedding, a3))
        # print("Similarity:", util.cos_sim(query_embedding, a4))


if __name__ == "__main__":
    MSMarcoEmbeddings()
