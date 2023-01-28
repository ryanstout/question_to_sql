import json
import re
import time

import snowflake.connector as connector

from python.sql.post_transform import PostTransform
from python.utils.logging import log


def setup_query_env(snowflake_cursor):
    snowflake_cursor.execute("use warehouse COMPUTE_WH;")
    snowflake_cursor.execute("use FIVETRAN_DATABASE.SHOPIFY;")


def run_query(snowflake_cursor, sql):
    try:
        log.debug("running query", sql=sql)

        if not re.search("\sLIMIT\s", sql):
            sql += " LIMIT 100"

        t1 = time.time()
        results = snowflake_cursor.execute(sql)

        # Copy data out now so we can reuse the cursor
        data = []
        for result in results:
            data.append(result)

        t2 = time.time()
        log.debug("query ran in: ", time=t2 - t1)

        # Return the result of the query, not the uses
        return data
    except connector.errors.ProgrammingError as e:
        log.error("snowflake connector programming error: ", error=e)
        return {"error": str(e)}
