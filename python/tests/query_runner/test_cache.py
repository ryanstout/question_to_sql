import json
import typing as t
from unittest.mock import patch

from python.query_runner import run_query
from python.utils.db import application_database_connection
from python.utils.redis import application_redis_connection

import prisma
from prisma.enums import DataSourceType
from prisma.types import DataSourceCreateInput

db = application_database_connection()
redis = application_redis_connection()

# TODO what is our *real* factory story here?
def make_data_source():
    return db.datasource.create(
        data=DataSourceCreateInput(
            name="snowflake",
            type=DataSourceType.SNOWFLAKE,
            # TODO not good, we should be able to pass in a dict
            credentials=t.cast(prisma.Json, json.dumps({"creds": "here"})),
        )
    )


@patch("python.query_runner.run_snowflake_query", return_value=[{"COUNT": 1}])
def test_caches_result(run_snowflake_query):
    data_source = make_data_source()
    results = run_query(data_source.id, "SELECT 1", allow_cached_queries=True)

    assert results == run_snowflake_query.return_value
    assert run_snowflake_query.call_count == 1

    keys = redis.keys()
    assert len(keys) == 1
    key = keys[0]
    json_str = redis.get(key)
    assert json_str is not None
    assert json.loads(json_str) == results


from python.query_runner import _cache_query_result


@patch("python.query_runner.run_snowflake_query", return_value=[{"COUNT": 1}])
def test_uses_cache(run_snowflake_query):
    sql = "SELECT * FROM ORDERS"
    data_source = make_data_source()

    _cache_query_result(
        data_source.id,
        sql,
        run_snowflake_query.return_value,
    )
    assert len(redis.keys()) == 1

    results = run_query(data_source.id, sql, allow_cached_queries=True)

    assert results == run_snowflake_query.return_value
    assert run_snowflake_query.call_count == 0
