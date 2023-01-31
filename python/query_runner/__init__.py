import typing as t

import snowflake.connector
from decouple import config
from prisma.enums import DataSourceType
from prisma.models import DataSource
from snowflake.connector.cursor import DictCursor

from prisma import Prisma
from python.utils.query_runner import run_query as run_query_old
from python.utils.query_runner import setup_query_env

# TODO this is a mess, will refactor once it's working

# TODO is there any reason why we wouldn't just have a single global db connection?
def dbConnection():
    db = Prisma()
    db.connect()
    return db


def run_query(data_source_id: int, sql: str) -> t.List[dict]:
    db = dbConnection()
    data_source = db.datasource.find_first(where={"id": data_source_id})

    assert data_source is not None

    if data_source.type == DataSourceType.SNOWFLAKE:
        return run_snowflake_query(data_source, sql)
    else:
        raise Exception("Unknown data source type: " + data_source.type)


def get_snowflake_cursor(data_source: DataSource):
    connection = snowflake.connector.connect(
        # pull these from the environment
        user=config("SNOWFLAKE_USERNAME"),
        password=config("SNOWFLAKE_PASSWORD"),
        account=config("SNOWFLAKE_ACCOUNT"),
    )

    cursor = connection.cursor(cursor_class=DictCursor)
    setup_query_env(cursor)

    return cursor, connection


def run_snowflake_query(data_source: DataSource, sql: str):
    cursor, connection = get_snowflake_cursor(data_source)

    results = run_query_old(cursor, sql)

    connection.close()
    return results
