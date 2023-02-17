import datetime
import time

import python.utils.db
from python.schema.ranker import Ranker
from python.schema.schema_builder import SchemaBuilder
from python.schema.simple_schema_builder import SimpleSchemaBuilder
from python.sql.exceptions import SqlInspectError
from python.sql.post_transform import PostTransform
from python.sql.sql_inspector import SqlInspector
from python.sql.types import SimpleSchema
from python.utils.batteries import log_execution_time
from python.utils.logging import log
from python.utils.openai_rate_throttled import openai_throttled

db = python.utils.db.application_database_connection()


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
        log.debug("Convert Question to SQL")

        # TODO: this could be cached on datasource or something
        simple_schema = SimpleSchemaBuilder().build(db, data_source_id)

        sql = question_with_schema_to_sql(simple_schema, table_schema_limited_by_token_size, question)
        log.debug("sql pre transform", sql=sql)

    # AST based transform of the SQL to fix up common issues
    with log_execution_time("ast transform"):
        sql = PostTransform(data_source_id).run(sql)

    log.debug("sql post transform", sql=sql)

    return sql


def question_with_schema_to_sql(
    simple_schema: SimpleSchema, schema: str, question: str, engine: str = "code-davinci-002"
) -> str:
    prompt = create_prompt(schema, question)

    log.debug("sending prompt to openai", prompt=prompt)

    stops = [";", "\n\n"]
    if engine == "text-chat-davinci-002-20230126":
        stops.append("<|im_end|>")  # chatgpt message end token

    while True:
        with log_execution_time("openai completion"):

            # See OpenAI completion docs for details on parameters:
            # https://platform.openai.com/docs/api-reference/completions/create
            result = openai_throttled.complete(
                engine=engine,
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

        ai_sql = f"SELECT {ai_sql};"

        # Verify that the ai sql is valud
        if is_sql_valid(simple_schema, ai_sql):
            break

    return ai_sql


def is_sql_valid(simple_schema: SimpleSchema, ai_sql: str) -> bool:
    """
    Returns true if the ai_sql is valid
    """

    try:
        SqlInspector(ai_sql, simple_schema)
    except SqlInspectError as e:
        log.warn("SQL is invalid", sql=ai_sql, error=e)
        return False

    return True


def create_prompt(schema: str, question: str) -> str:
    """
    Takes in the schema and question and returns the prompt string
    """

    def generate_date_suffix(n):
        if 10 <= n % 100 < 20:
            return "th"

        return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")

    day_int = datetime.datetime.now().day
    suffix = generate_date_suffix(day_int)

    # current date in the format of 'January 28th, 2023'
    # the date format here is picked in a very specific fashion
    current_date = datetime.datetime.now().strftime(f"%B %-d{suffix}, %Y")

    prompt_parts = [
        f"-- {PostTransform.in_dialect.capitalize()} SQL schema",
        schema,
        "",
        "-- How many orders are there per month?",
        'SELECT\n  COUNT(*) AS orders_per_month,\n  EXTRACT(MONTH FROM created_at) AS month\nFROM "order"\nGROUP BY\n  month\nORDER BY\n  month NULLS LAST;',
        "",
        "-- Which product sells the best?",
        """SELECT
    COUNT(*) AS orders_per_product,
    product.title
FROM "order"
JOIN order_line
    ON order_line.order_id = "order".id
JOIN product_variant
    ON product_variant.id = order_line.variant_id
JOIN product
    ON product.id = product_variant.product_id
GROUP BY
    product.title
ORDER BY
orders_per_product DESC NULLS FIRST;
        """,
        "",
        # "-- Calculate lifetime of a customer by taking the duration between the first and most recent order for a customer. ",
        # "-- If we're returning a day, always also return the month and year"
        # f"-- Assuming the current date is {current_date}",
        # "-- using NOW() instead of dates\n\n",
        f"-- {question}",
        "SELECT ",
    ]

    prompt = "\n".join(prompt_parts)
    return prompt
