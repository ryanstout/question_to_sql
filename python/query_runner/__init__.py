import json
import pickle
from typing import Any, Dict, List, TypeAlias, TypeGuard

import xxhash

from python.utils.db import application_database_connection
from python.utils.logging import log
from python.utils.redis import application_redis_connection

from prisma.enums import DataSourceType
from prisma.models import DataSource

from .snowflake import run_snowflake_query

SnowflakeResponse: TypeAlias = List[Dict[str, Any]]

redis = application_redis_connection()


def is_correct_snowflake_result(val: object) -> TypeGuard[SnowflakeResponse]:
    """
    We expect snowflake queries to return a list of dicts
    """
    if isinstance(val, dict):
        return True

    if not isinstance(val, list):
        return False

    return all(isinstance(x, dict) for x in val)


def _query_cache_key(data_source_id: int, sql: str) -> str:
    hashed_sql = xxhash.xxh64(sql).hexdigest()
    return f"query-cache-{data_source_id}-{hashed_sql}"


def _cached_query_result(data_source_id: int, sql: str) -> None | list[dict]:
    cached_query_result = redis.get(_query_cache_key(data_source_id, sql))

    if cached_query_result:
        log.debug("query cache hit")
        return pickle.loads(cached_query_result)


def _cache_query_result(data_source_id: int, sql: str, result: list[dict]):
    redis.setex(
        _query_cache_key(data_source_id, sql),
        # 48hr is completely arbitrary and is geared towards the import script
        60 * 60 * 24 * 2,
        pickle.dumps(result),
    )


# TODO allow data_source to be passed in
def run_query(data_source_id: int, sql: str, allow_cached_queries=False, **kwargs) -> list[dict]:
    db = application_database_connection()

    data_source = db.datasource.find_first(where={"id": data_source_id})
    assert data_source is not None

    if allow_cached_queries and (cached_result := _cached_query_result(data_source_id, sql)):
        return cached_result

    if data_source.type == DataSourceType.SNOWFLAKE:
        result = run_snowflake_query(data_source, sql, **kwargs)

        if is_correct_snowflake_result(result):
            _cache_query_result(data_source_id, sql, result)
            return result
        else:
            raise TypeError("Unexpected snowflake return type: " + str(type(result)))

    else:
        raise Exception("Unknown data source type: " + data_source.type)
