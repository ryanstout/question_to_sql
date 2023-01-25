import json

import snowflake.connector as connector

from python.sql.post_transform import PostTransform


def run_query(snowflake_cursor, sql):
    try:
        result = snowflake_cursor.execute(sql)

        return json.dumps(result)
    except connector.errors.ProgrammingError as e:
        return str(e)
