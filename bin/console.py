#!/usr/bin/env python
from python.setup import log

import json

import IPython
import query_runner
from decouple import config
from utils.db import application_database_connection

from python.query_runner.snowflake import get_snowflake_cursor

from prisma.enums import DataSourceType
from prisma.types import DataSourceCreateInput


def create_datasource_from_environment():
    return db.datasource.create(
        data=DataSourceCreateInput(
            name="snowflake",
            type=DataSourceType.SNOWFLAKE,
            # TODO not good, we should be able to pass in a dict
            credentials=json.dumps(
                {
                    "username": config("SNOWFLAKE_USERNAME"),
                    "password": config("SNOWFLAKE_PASSWORD"),
                    "account": config("SNOWFLAKE_ACCOUNT"),
                    "warehouse": config("SNOWFLAKE_WAREHOUSE"),
                    "database": config("SNOWFLAKE_DATABASE"),
                    "schema": config("SNOWFLAKE_SCHEMA"),
                }
            ),
        )
    )


def get_data_source(id: int):
    return db.datasource.find_first(where={"id": id})


def test_snowflake_connection(data_source_id: int):
    get_snowflake_cursor(get_data_source(data_source_id))


db = application_database_connection()

IPython.start_ipython(user_ns=locals())
