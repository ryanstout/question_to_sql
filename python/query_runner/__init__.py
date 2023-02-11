from typing import Any, Dict, List, TypeAlias, TypeGuard

from utils.db import application_database_connection

from prisma.enums import DataSourceType
from prisma.models import DataSource

from .snowflake import run_snowflake_query

SnowflakeResponse: TypeAlias = List[Dict[str, Any]]


def is_correct_snowflake_result(val: object) -> TypeGuard[SnowflakeResponse]:
    """
    We expect snowflake queries to return a list of dicts
    """
    if not isinstance(val, list):
        return False

    return all(isinstance(x, dict) for x in val)


# TODO allow data_source to be passed in
def run_query(data_source_id: int, sql: str, **kwargs) -> list[dict]:
    db = application_database_connection()
    data_source = db.datasource.find_first(where={"id": data_source_id})

    assert data_source is not None

    if data_source.type == DataSourceType.SNOWFLAKE:
        result = run_snowflake_query(data_source, sql, **kwargs)

        if is_correct_snowflake_result(result):
            return result
        else:
            raise TypeError("Unexpected snowflake return type: " + str(type(result)))

    else:
        raise Exception("Unknown data source type: " + data_source.type)
