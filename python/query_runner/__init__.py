import pickle

import xxhash

from python.utils.db import application_database_connection
from python.utils.logging import log
from python.utils.redis import application_redis_connection

from prisma.enums import DataSourceType

from .snowflake import run_snowflake_query

redis = application_redis_connection()


def _query_cache_key(data_source_id: int, sql: str) -> str:
    hashed_sql = xxhash.xxh64(sql).hexdigest()
    return f"query-cache-{data_source_id}-{hashed_sql}"


def _cached_query_result(data_source_id: int, sql: str) -> None | list[dict]:
    cache_key = _query_cache_key(data_source_id, sql)
    cached_query_result = redis.get(cache_key)

    if cached_query_result:
        log.debug("query cache hit")
        return pickle.loads(cached_query_result)

    return None


def _cache_query_result(data_source_id: int, sql: str, result: list[dict]):
    # TODO we need to wrap all redis calls in a protection block like this
    try:
        redis.setex(
            _query_cache_key(data_source_id, sql),
            # 48hr is completely arbitrary and is geared towards the import script
            60 * 60 * 24 * 2,
            # TODO since the result is returned as JSON, shouldn't we be able to store it as JSON?
            pickle.dumps(result),
        )
    except Exception as e:
        log.error("failed to cache query result: " + str(e))


# TODO allow data_source record to be passed in
def run_query(data_source_id: int, sql: str, allow_cached_queries=False, **kwargs) -> list[dict]:
    db = application_database_connection()

    data_source = db.datasource.find_first(where={"id": data_source_id})
    assert data_source is not None

    if allow_cached_queries and (cached_result := _cached_query_result(data_source_id, sql)):
        return cached_result

    if data_source.type == DataSourceType.SNOWFLAKE:
        result = run_snowflake_query(data_source, sql, **kwargs)

        if allow_cached_queries:
            _cache_query_result(data_source_id, sql, result)

        return result

    raise RuntimeError("Unknown data source type: " + data_source.type)
