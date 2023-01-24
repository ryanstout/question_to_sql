import openai
from decouple import config
from schema.schema_builder import SchemaBuilder

from python.schema.ranker import Ranker
from python.utils.connections import Connections

openai.api_key = config("OPENAI_KEY")


def question_with_data_source_to_sql(data_source_id: int, question: str) -> str:
    connections = Connections()
    db = connections.open()

    ranked_structure = Ranker(db, data_source_id).rank(question)
    table_schema_limited_by_token_size = SchemaBuilder(db).build(ranked_structure)
    sql = question_with_schema_to_sql(question, table_schema_limited_by_token_size)
    return sql


def question_with_schema_to_sql(schema: str, question: str) -> str:
    prompt = f"{question}\n\n{schema}"

    result = openai.Completion.create(
        engine="code-davinci-002",
        prompt=prompt,
        max_tokens=1024,  # was 256
        temperature=0.0,
        top_p=1,
        presence_penalty=0,
        frequency_penalty=0,
        best_of=1,
        n=1,
        stream=False,
        stop=[";", "\n\n"],
    )

    return result
