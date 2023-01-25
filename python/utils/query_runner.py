import json

import snowflake.connector as connector

from python.sql.post_transform import PostTransform
from python.utils.logging import log


def run_query(snowflake_cursor, sql):
    try:

        log.debug("running query", sql=sql)
        result = snowflake_cursor.execute(sql)
        log.debug("result: ", result=result)

        return json.dumps(result)
    except connector.errors.ProgrammingError as e:
        log.error("snowflake connector programming error: ", error=e)
        return str(e)
