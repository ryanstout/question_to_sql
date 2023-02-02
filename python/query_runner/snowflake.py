from python.setup import log

import re

import snowflake.connector
from decouple import config
from sentry_sdk import capture_exception
from snowflake.connector.cursor import DictCursor, SnowflakeCursor

from python.utils.batteries import log_execution_time, not_none

from prisma.models import DataSource


def get_snowflake_cursor(data_source: DataSource):
    connection = snowflake.connector.connect(
        # pull these from the environment
        user=config("SNOWFLAKE_USERNAME"),
        password=config("SNOWFLAKE_PASSWORD"),
        account=config("SNOWFLAKE_ACCOUNT"),
    )

    cursor = connection.cursor(cursor_class=DictCursor)

    # TODO should pull from datasource credentials
    cursor.execute("use warehouse COMPUTE_WH;")
    cursor.execute("use FIVETRAN_DATABASE.SHOPIFY;")

    return cursor, connection


def get_query_results(cursor: SnowflakeCursor, sql: str):
    try:
        if not re.search("\sLIMIT\s", sql):
            sql += " LIMIT 100"

        log.debug("running query", sql=sql)

        with log_execution_time("snowflake query runtime"):
            results = not_none(cursor.execute(sql)).fetchall()

        # Return the result of the query, not the uses
        return results
    except Exception as e:
        capture_exception(e)
        # TODO I wonder if sentry logs the error and we don't need to do this?
        log.exception("snowflake connector programming error")
        return {"error": str(e)}


def run_snowflake_query(data_source: DataSource, sql: str):
    cursor, connection = get_snowflake_cursor(data_source)

    results = get_query_results(cursor, sql)

    connection.close()
    return results
