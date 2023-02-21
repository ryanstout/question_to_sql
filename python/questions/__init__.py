import datetime
import time

import python.utils.db
from python.schema.ranker import Ranker
from python.schema.schema_builder import SchemaBuilder
from python.schema.simple_schema_builder import SimpleSchemaBuilder
from python.sql.exceptions import SqlInspectError
from python.sql.sql_inspector import SqlInspector
from python.sql.sql_parser import SqlParser
from python.sql.sql_resolve_and_fix import SqlResolveAndFix
from python.sql.types import SimpleSchema
from python.utils.batteries import log_execution_time
from python.utils.logging import log
from python.utils.openai_rate_throttled import openai_throttled

db = python.utils.db.application_database_connection()


def question_with_data_source_to_sql(data_source_id: int, question: str, engine: str = "code-davinci-002") -> str:
    ranked_structure = Ranker(db, data_source_id).rank(question)
    log.debug("building schema")

    with log_execution_time("schema build"):
        table_schema_limited_by_token_size = SchemaBuilder(db, engine).build(data_source_id, ranked_structure)

    log.debug("convert question and schema to sql")
    with log_execution_time("schema to sql"):
        log.debug("Convert Question to SQL")

        # TODO: this could be cached on datasource or something
        simple_schema = SimpleSchemaBuilder().build(db, data_source_id)

        sql = question_with_schema_to_sql(simple_schema, table_schema_limited_by_token_size, question)

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

    run_count = 0
    temperature = 0.0
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
                temperature=temperature,
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

        log.debug("sql pre transform", ai_sql=ai_sql)

        # Verify that the ai sql is valud
        ai_sql = fixup_sql(simple_schema, ai_sql)
        if ai_sql:
            # If we got back None, try the next result
            break
        else:
            # If we got back None, try the next result
            run_count += 1

            # If openAI is generating invalid sql queries, we could increase N and work our way down, but this will
            # run us out of tokens pretty quickly. Instead we bump the temperature a bit and try again.
            #
            # TODO: if OpenAI ever bumps the token limits, we should switch to taking N. Might be worth creating a
            # smaller prompt and then trying to generate more results.
            temperature += 0.03

            if run_count > 4:
                break

    if ai_sql is None:
        raise ValueError("OpenAI failed to generate a valid SQL query")

    return ai_sql


def fixup_sql(simple_schema: SimpleSchema, ai_sql: str) -> str | None:
    """
    Returns fixed sql if it is valid, otherwise returns None
    """

    with log_execution_time("sql fix up"):
        try:
            sql = SqlResolveAndFix().run(ai_sql, simple_schema)
            return sql
        except SqlInspectError as e:
            # A SqlInspectError means the sql will not run correctly at run time. This is usually due to a non-existent
            # table or column being referenced, or just invalid sql.
            log.warn("SQL is invalid", sql=ai_sql, error=e)
            return None


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
        f"-- {SqlParser.in_dialect.capitalize()} SQL schema",
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
        "-- A few rules for building SQL queries: ",
        "-- Return `SELECT 'unsure'` if we don't know how to answer the question",
        # "-- 1. Do case insensitive matches using LOWER unless the case matters",
        # "-- Calculate lifetime of a customer by taking the duration between the first and most recent order for a customer. ",
        # "-- If we're returning a day, always also return the month and year"
        # f"-- Assuming the current date is {current_date}",
        # "-- using NOW() instead of dates\n\n",
        "",
        "",
        f"-- {question}",
        "SELECT ",
    ]

    prompt = "\n".join(prompt_parts)
    return prompt
