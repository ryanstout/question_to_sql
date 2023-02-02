import typing as t

from utils.db import application_database_connection

from prisma.enums import DataSourceType
from prisma.models import DataSource

from .snowflake import run_snowflake_query


# TODO allow data_source to be passed in
def run_query(data_source_id: int, sql: str) -> t.List[dict]:
    db = application_database_connection()
    data_source = db.datasource.find_first(where={"id": data_source_id})

    assert data_source is not None

    if data_source.type == DataSourceType.SNOWFLAKE:
        return run_snowflake_query(data_source, sql)
    else:
        raise Exception("Unknown data source type: " + data_source.type)
