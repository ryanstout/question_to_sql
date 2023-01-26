import openai
from backoff_utils import apply_backoff
from decouple import config

from python.schema.ranker import Ranker
from python.schema.schema_builder import SchemaBuilder
from python.sql.post_transform import PostTransform
from python.utils.connections import Connections
from python.utils.logging import log

openai.api_key = config("OPENAI_KEY")


from python.setup import log

import typing as t


def question_with_data_source_to_sql(data_source_id: int, question: str) -> str:
    connections = Connections()
    db = connections.open()

    ranked_structure = Ranker(db, data_source_id).rank(question)
    log.debug("Building Schema")
    table_schema_limited_by_token_size = SchemaBuilder(db).build(ranked_structure)
    log.debug("Convert Question to SQL")
    sql = question_with_schema_to_sql(table_schema_limited_by_token_size, question)
    log.debug("SQL pre transform: ", sql=sql)

    # AST based tranform of the SQL to fix up common issues
    sql = PostTransform(data_source_id).run(sql)

    log.debug("SQL post transform: ", sql=sql)

    return sql


class ChoicesItem(t.TypedDict):
    finish_reason: str
    index: int
    logprobs: None
    text: str


class Usage(t.TypedDict):
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int


class OpenAIResponse(t.TypedDict):
    choices: t.List[ChoicesItem]
    created: int
    id: str
    model: str
    object: str
    usage: Usage


@apply_backoff(max_tries=5)
def question_with_schema_to_sql(schema: str, question: str) -> str:
    prompt = f"-- Postgres SQL schema\n{schema}\n\n-- {question}\nSELECT "

    log.debug("sending prompt to openai", prompt=prompt)

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
        # tells the model to stop generating a response when it gets to the end of the SQL
        stop=[";", "\n\n"],
    )

    result = t.cast(OpenAIResponse, result)

    if len(result.choices) > 1:
        # noop
        pass

    ai_sql = result.choices[0].text
    return f"SELECT {ai_sql};"
