from python.setup import log

import re
import typing as t

import snowflake.connector
from decouple import config
from sentry_sdk import capture_exception
from snowflake.connector.cursor import DictCursor, SnowflakeCursor

from python.utils.batteries import log_execution_time, not_none

from prisma.models import DataSource


class SnowflakeCredentials(t.TypedDict):
    username: str
    password: str
    account: str
    warehouse: str
    database: str
    schema: str


def get_snowflake_cursor(data_source: DataSource):
    snowflake_credentials = t.cast(SnowflakeCredentials, data_source.credentials)

    connection = snowflake.connector.connect(
        user=snowflake_credentials["username"],
        password=snowflake_credentials["password"],
        account=snowflake_credentials["account"],
    )

    cursor = connection.cursor(cursor_class=DictCursor)

    cursor.execute(f"use warehouse {snowflake_credentials['warehouse']};")
    cursor.execute(f"use {snowflake_credentials['database']}.{snowflake_credentials['schema']};")

    return cursor, connection


def get_query_results(cursor: SnowflakeCursor, sql: str):
    try:
        if not re.search(r"\sLIMIT\s", sql):
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
