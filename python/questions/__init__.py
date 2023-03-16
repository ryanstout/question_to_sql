import datetime
import re
import typing as t

import sentry_sdk
from decouple import config
from sqlglot.errors import ParseError

import python.utils.db
from python.prompts.chat_prompt import ChatPrompt
from python.prompts.codex_prompt import CodexPrompt
from python.prompts.prompt import Prompt
from python.questions.indexes_and_models import IndexesAndModels
from python.schema.learned_ranker import LearnedRanker
from python.schema.ranker import Ranker
from python.schema.schema_builder import SchemaBuilder
from python.schema.simple_schema_builder import build_simple_schema
from python.sql.exceptions import SqlInspectError
from python.sql.sql_parser import SqlParser
from python.sql.sql_resolve_and_fix import SqlResolveAndFix
from python.sql.types import SimpleSchema
from python.utils.batteries import log_execution_time
from python.utils.indexes_and_models import application_indexes_and_models
from python.utils.logging import log
from python.utils.openai import OpenAIEngineOptions, is_chat_engine, openai_engine
from python.utils.openai_rate_throttled import openai_throttled

db = python.utils.db.application_database_connection()

use_learned_ranker = config("ENABLE_LEARNED_RANKER", default=True, cast=bool)
retry_openai_variants = config("ENABLE_OPENAI_VARIANT_RETRY", default=False, cast=bool)

# Instantiate a singleton instance to load all indexes and models into ram once per process
indexes_and_models = application_indexes_and_models()


def question_with_data_source_to_sql(
    data_source_id: int, question: str, engine: OpenAIEngineOptions | None = None
) -> str:
    ranked_schema = indexes_and_models.ranker(data_source_id).rank(question)

    log.debug("building schema")

    if not engine:
        engine = openai_engine()

    if is_chat_engine(engine):
        prompt_generator = ChatPrompt(engine, data_source_id, ranked_schema, question)
    else:
        prompt_generator = CodexPrompt(engine, data_source_id, ranked_schema, question)

    with log_execution_time("prompt generation"):
        prompt = prompt_generator.generate()

    with log_execution_time("question to sql"):
        simple_schema = build_simple_schema(data_source_id)
        sql = _question_with_prompt(simple_schema, prompt, engine)

    log.debug("sql post transform", sql=sql)

    return sql


def _question_with_prompt(
    simple_schema: SimpleSchema, prompt: str | list[dict[str, str]], engine: OpenAIEngineOptions
) -> str:
    stops = [";", "\n\n"]

    run_count = 0
    temperature = 0.0

    while True:
        ai_sql = ""
        with log_execution_time("openai completion"):

            # See OpenAI completion docs for details on parameters:
            # https://platform.openai.com/docs/api-reference/completions/create
            if is_chat_engine(engine):
                result = openai_throttled.complete(
                    model=engine,
                    messages=prompt,
                    temperature=temperature,
                    top_p=1,
                    n=1,
                    max_tokens=1000,
                    presence_penalty=0,
                    frequency_penalty=0,
                )

                # TODO adjust the `ChoicesItem` to include turbo responses
                result = t.cast(dict, result)

                ai_sql = result["choices"][0]["message"]["content"]

                # Extract inside of backticks if backticks are present
                if "```" in ai_sql:
                    content_between_backticks = re.findall(r"```(?:sql)?(.*?)```", ai_sql, re.M | re.S)
                    ai_sql = content_between_backticks[0]
            else:

                result = openai_throttled.complete(
                    engine=engine,
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
            print("RESULTS: ", result)

        ai_sql = ai_sql.replace("`", '"')  # sometimes we get backticks instead of quotes
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
        except ParseError:
            # Sqlglot parse error, sometimes this is a message from chatgpt on why it couldn't generate things.
            return ai_sql
        except SqlInspectError as e:
            # A SqlInspectError means the sql will not run correctly at run time. This is usually due to a non-existent
            # table or column being referenced, or just invalid sql.
            sentry_sdk.capture_exception(e, extras={"ai_sql": ai_sql})
            log.warn("SQL is invalid", sql=ai_sql, error=e)
            return None
        except RuntimeError:
            # SqlGlot has some errors that don't get wrapped and come back as a runtime error
            return ai_sql
