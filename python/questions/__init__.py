import datetime

import python.utils.db
from python.schema.ranker import Ranker
from python.schema.schema_builder import SchemaBuilder
from python.sql.post_transform import PostTransform
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
        sql = question_with_schema_to_sql(table_schema_limited_by_token_size, question)

    log.debug("sql pre transform", sql=sql)

    # AST based transform of the SQL to fix up common issues
    with log_execution_time("ast transform"):
        sql = PostTransform(data_source_id).run(sql)

    log.debug("sql post transform", sql=sql)

    return sql


def question_with_schema_to_sql(schema: str, question: str, engine: str = "code-davinci-002") -> str:
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
        # "-- Treat the tables listed below in order of priority, highest priority being listed first",
        f"-- Assuming the current date is {current_date}",
        # an extra line break hints to the model that what comes next is different and should be treated as something different
        "-- using NOW() instead of dates\n\n",
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
