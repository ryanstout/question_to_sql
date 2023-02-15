import utils

from python.schema.ranker import Ranker
from python.schema.schema_builder import SchemaBuilder
from python.sql.post_transform import PostTransform
from python.utils.batteries import log_execution_time
from python.utils.logging import log
from python.utils.openai_rate_throttled import openai_throttled

db = utils.db.application_database_connection()


def question_with_data_source_to_sql(data_source_id: int, question: str, engine: str = "code-davinci-002") -> str:
    ranked_structure = Ranker(db, data_source_id).rank(question)
    log.debug("building schema")

    # ob = cProfile.Profile()
    # ob.enable()
    with log_execution_time("schema build"):
        table_schema_limited_by_token_size = SchemaBuilder(db, engine).build(data_source_id, ranked_structure)
    # ob.disable()
    # sec = io.StringIO()
    # sortby = SortKey.CUMULATIVE
    # ps = pstats.Stats(ob, stream=sec).sort_stats(sortby)
    # ps.print_stats()

    # print(sec.getvalue())

    log.debug("convert question and schema to sql")
    with log_execution_time("schema to sql"):
        sql = question_with_schema_to_sql(table_schema_limited_by_token_size, question)

    # AST based transform of the SQL to fix up common issues
    with log_execution_time("ast transform"):
        sql = PostTransform(data_source_id).run(sql)

    log.debug("sql post transform", sql=sql)

    return sql


def question_with_schema_to_sql(schema: str, question: str, engine: str = "code-davinci-002") -> str:
    prompt_parts = [
        f"-- {PostTransform.in_dialect.capitalize()} SQL schema",
        schema,
        "",
        # TODO is this few shot learning? Can we extract this out?
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

    stops = [";", "\n\n"]
    if engine == "text-chat-davinci-002-20230126":
        stops.append("<|im_end|>")  # chatgpt message end token

    result = openai_throttled.complete(
        engine=engine,
        # TODO convert to string enum and document there instead
        # engine="code-davinci-002",
        # engine="text-chat-davinci-002-20230126",  # leaked chatgpt model
        prompt=prompt,
        max_tokens=1024,  # was 256
        temperature=0.0,
        top_p=1,
        presence_penalty=0,
        frequency_penalty=0,
        best_of=1,
        # logprobs=4,
        n=1,
        stream=False,
        # tells the model to stop generating a response when it gets to the end of the SQL
        stop=stops,
    )

    ai_sql = result["choices"][0]["text"]
    return f"SELECT {ai_sql};"
