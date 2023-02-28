import datetime
import os

import sentry_sdk
from decouple import config

import python.utils.db
from python.schema.learned_ranker import LearnedRanker
from python.schema.ranker import Ranker
from python.schema.schema_builder import SchemaBuilder
from python.schema.simple_schema_builder import SimpleSchemaBuilder
from python.sql.exceptions import SqlInspectError
from python.sql.sql_parser import SqlParser
from python.sql.sql_resolve_and_fix import SqlResolveAndFix
from python.sql.types import SimpleSchema
from python.utils.batteries import log_execution_time
from python.utils.logging import log
from python.utils.openai_rate_throttled import openai_throttled

db = python.utils.db.application_database_connection()

use_learned_ranker = config("ENABLE_LEARNED_RANKER", default=True, cast=bool)
retry_openai_variants = config("ENABLE_OPENAI_VARIANT_RETRY", default=False, cast=bool)


def question_with_data_source_to_sql(data_source_id: int, question: str, engine: str = "code-davinci-002") -> str:
    if use_learned_ranker:
        ranked_structure = LearnedRanker(data_source_id).rank(question)
    else:
        ranked_structure = Ranker(data_source_id).rank(question)
    log.debug("building schema")

    with log_execution_time("schema build"):
        table_schema_limited_by_token_size = SchemaBuilder(db, engine).build(data_source_id, ranked_structure)

    log.debug("convert question and schema to sql")
    with log_execution_time("schema to sql"):
        simple_schema = SimpleSchemaBuilder().build(db, data_source_id)
        sql = _question_with_schema_to_sql(simple_schema, table_schema_limited_by_token_size, question, engine)

    log.debug("sql post transform", sql=sql)

    return sql


def _question_with_schema_to_sql(
    simple_schema: SimpleSchema, schema: str, question: str, engine: str = "code-davinci-002"
) -> str:
    prompt = _create_prompt(schema, question)

    log.debug("sending prompt to openai", prompt=prompt)

    stops = [";", "\n\n"]
    if engine == "text-chat-davinci-002-20230126":
        stops.append("<|im_end|>")  # chatgpt message end token
        log.debug("using chatgpt model")

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
        ai_sql = _fixup_sql(simple_schema, ai_sql)

        if ai_sql:
            # If we got back None, try the next result
            break

        if not retry_openai_variants:
            break

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


def _fixup_sql(simple_schema: SimpleSchema, ai_sql: str) -> str | None:
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
            sentry_sdk.capture_exception(e, extras={"ai_sql": ai_sql})
            log.warn("SQL is invalid", sql=ai_sql, error=e)
            return None


def _create_prompt(
    schema: str,
    question: str,
    use_global_instruct: bool = True,
    use_rules: bool = True,
    use_few_shot: bool = True,
    use_comments: bool = True,
    use_backticks: bool = False,
) -> str:
    """
    Takes in the schema and question and returns the prompt string
    """

    # The tripple backtick wrapper can be useful in some cases
    backticks = "```" if use_backticks else ""
    comments = "-- " if use_comments else ""

    def generate_date_suffix(n):
        if 10 <= n % 100 < 20:
            return "th"

        return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")

    day_int = datetime.datetime.now().day
    suffix = generate_date_suffix(day_int)

    # current date in the format of 'January 28th, 2023'
    # the date format here is picked in a very specific fashion
    current_date = datetime.datetime.now().strftime(f"%B %-d{suffix}, %Y")

    schema_parts = [f"{comments}{SqlParser.in_dialect.capitalize()} SQL schema", f"{backticks}{schema}{backticks}", ""]

    if use_rules:
        rule_num: int = 0

        def rule_prefix():
            nonlocal rule_num
            rule_num += 1
            return f"{rule_num}. "

        rules = [
            "",
            f"{backticks}",
            # f"{comments}Rules for building SQL queries: ",
            f"{comments}Rules: ",
            f"{comments}{rule_prefix()}Return `SELECT 'unsure'` if we don't know how to answer the question",
            # f"{comments}{rule_prefix()}Do case insensitive matches using LOWER unless the case matters or it matches a possible value",
            f"{comments}{rule_prefix()}When matching a string, use LOWER unless it matches a listed possible value",
            # f"{comments}{rule_prefix()}Calculate lifetime of a customer by taking the duration between the first and most recent order for a customer. ",
            f"{comments}{rule_prefix()}If we're returning a day, always also return the month and year",
            f"{comments}{rule_prefix()}Add ORDER BY to every SELECT",  # makes things deterministic
            # In snowflake, Count(*), etc.. are not allowed directly in a ORDER BY or HAVING, they have to be in the
            # SELECT expression first, then accessed by alias.
            f"{comments}{rule_prefix()}COUNT's used in ORDER BY or HAVING should appear in the SELECT first.",
            f"{comments}{rule_prefix()}Any columns used must be in the Schema",
            f"{comments}{rule_prefix()}Assume the current date is {current_date}",
            f"{comments}{rule_prefix()}use NOW() instead of dates",
            f"{backticks}",
            "",
        ]
    else:
        rules = []

    if use_global_instruct:
        question_prefix = "Question: "
    else:
        question_prefix = ""

    if use_few_shot:
        few_shot = [
            f"{comments}{question_prefix}How many orders are there per month?",
            f"""{backticks}SELECT
  COUNT(*) AS orders_per_month,
  EXTRACT(MONTH FROM "order".created_at) AS month
FROM "order"
GROUP BY
  month
ORDER BY
  month;{backticks}""",
            "",
            f"{comments}{question_prefix}Question: Which product sells the best?",
            f"""{backticks}SELECT
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
    product.id,
    product.title
ORDER BY
orders_per_product DESC;{backticks}
            """,
            "",
            f"{comments}{question_prefix}Are sales of the cross atx fountain pen - matte chrome increasing or decreasing?",
            f"""{backticks}SELECT
    COUNT(*) AS orders_per_month,
    EXTRACT(MONTH FROM "ORDER".created_at) AS month
FROM "order"
JOIN order_line
    ON order_line.order_id = "order".id
JOIN product_variant
    ON product_variant.id = order_line.variant_id
JOIN product
    ON product.id = product_variant.product_id
WHERE
    product.title = 'Cross ATX Fountain Pen - Matte Chrome'
GROUP BY
    month
ORDER BY
    month;{backticks}""",
            "",
            "",
            f"""{comments}{question_prefix}What products are pen and pencil sets""",
            f"""{backticks}SELECT DISTINCT
  product.title
FROM product
JOIN product_tag
  ON product_tag.product_id = product.id
WHERE
  product_tag.value = 'Collection_Pen and Pencil Set'
ORDER BY
  product.title;{backticks}""",
        ]
    else:
        few_shot = []

    select_prefix = [
        f"{comments}{question_prefix}{question}",
        f"{backticks}SELECT ",
    ]

    prompt_parts: list[str] = []

    if use_global_instruct:
        prompt_parts += [
            f"{comments}Given a Schema, and a Question, generate a correct SQL query that answers the question using the Schema. The SQL query must follow the Rules provided.",
            "",
        ]
    prompt_parts += schema_parts
    prompt_parts += few_shot
    prompt_parts += rules
    prompt_parts += select_prefix

    prompt = "\n".join(prompt_parts)
    return prompt
