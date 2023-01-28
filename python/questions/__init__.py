import cProfile
import time

import backoff
import openai
from decouple import config
from openai.error import OpenAIError

from python.schema.ranker import Ranker
from python.schema.schema_builder import SchemaBuilder
from python.sql.post_transform import PostTransform
from python.utils.connections import Connections
from python.utils.logging import log

openai.api_key = config("OPENAI_KEY")


from python.setup import log

import io
import pstats
import typing as t
from pstats import SortKey


def question_with_data_source_to_sql(data_source_id: int, question: str) -> str:
    connections = Connections()
    db = connections.open()

    ranked_structure = Ranker(db, data_source_id).rank(question)
    log.debug("Building Schema")
    t1 = time.time()

    # ob = cProfile.Profile()
    # ob.enable()
    table_schema_limited_by_token_size = SchemaBuilder(db).build(data_source_id, ranked_structure)
    # ob.disable()
    # sec = io.StringIO()
    # sortby = SortKey.CUMULATIVE
    # ps = pstats.Stats(ob, stream=sec).sort_stats(sortby)
    # ps.print_stats()

    # print(sec.getvalue())

    t2 = time.time()
    log.debug("Built scema in ", time=t2 - t1)
    log.debug("Convert Question to SQL")
    sql = question_with_schema_to_sql(table_schema_limited_by_token_size, question)
    t3 = time.time()
    log.debug("SQL pre transform: ", sql=sql, time=t3 - t2)

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


@backoff.on_exception(backoff.expo, OpenAIError, factor=60, max_tries=5, logger=log)
def question_with_schema_to_sql(schema: str, question: str) -> str:
    prompt_parts = [
        f"-- {PostTransform.in_dialect.capitalize()} SQL schema",
        schema,
        "",
        "-- How many orders are there per month?",
        'SELECT\n  COUNT(*) AS orders_per_month,\n  EXTRACT(MONTH FROM created_at) AS month\nFROM "ORDER"\nGROUP BY\n  month\nORDER BY\n  month NULLS LAST',
        "",
        "-- Which product sells the best?",
        """SELECT
  COUNT(*) AS orders_per_product,
  PRODUCT.title
FROM "ORDER"
JOIN ORDER_LINE
  ON ORDER_LINE.order_id = "ORDER".id
JOIN PRODUCT_VARIANT
  ON PRODUCT_VARIANT.id = ORDER_LINE.variant_id
JOIN PRODUCT
  ON PRODUCT.id = PRODUCT_VARIANT.product_id
GROUP BY
  PRODUCT.title
ORDER BY
orders_per_product DESC NULLS FIRST""",
        "",
        # "-- Assuming the current date is January 28th, 2023",
        # "-- using NOW() instead of dates\n\n",
        f"-- {question}",
        "SELECT ",
    ]

    prompt = "\n".join(prompt_parts)

    log.debug("sending prompt to openai", prompt=prompt)

    t1 = time.time()
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

    t2 = time.time()
    log.debug("openai completion in", time=t2 - t1)

    ai_sql = result.choices[0].text
    return f"SELECT {ai_sql};"
