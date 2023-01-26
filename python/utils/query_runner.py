import json

import snowflake.connector as connector

from python.sql.post_transform import PostTransform
from python.utils.logging import log


def setup_query_env(snowflake_cursor):
    snowflake_cursor.execute("use warehouse COMPUTE_WH;")
    snowflake_cursor.execute("use FIVETRAN_DATABASE.SHOPIFY;")


def run_query(snowflake_cursor, sql):
    try:
        log.debug("running query", sql=sql)
        results = snowflake_cursor.execute(sql)
        log.debug("result: ", results=results)

        # Copy data out now so we can reuse the cursor
        data = []
        for result in results:
            data.append(result)

        # Return the result of the query, not the uses
        return data
    except connector.errors.ProgrammingError as e:
        log.error("snowflake connector programming error: ", error=e)
        return str(e)
