from python.embeddings.ann_search import AnnSearch
from python.embeddings.embedding import generate_embedding
from python.embeddings.openai_embedder import OpenAIEmbedder
from python.sql.types import DbElementIds


class FewShotEmbeddingSearch:
    def __init__(self, data_source_id: int, path: str):
        self.path = path
        self.index = AnnSearch(path)

    def search(self, question: str, number_of_matches: int, embedder=OpenAIEmbedder) -> list[int]:
        query_embedding = generate_embedding(question, embedder=embedder, cache_results=True)

        results: list[int] = []

        for (_score, db_element_holder) in self.index.search(query_embedding, number_of_matches):
            # We use the same tooling from the main embedding, so the question id comes in as the table value in a
            # DbElementIds object.
            results.append(db_element_holder.table)

        return results
