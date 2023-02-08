from python.setup import log

import json
import re
from multiprocessing.pool import ThreadPool

import click
import utils
from decouple import config

import python.utils.sql as sql
from python.embeddings.embedding_builder import EmbeddingBuilder
from python.utils.logging import log
from python.utils.sql import unqualified_table_name

from prisma import Prisma
from prisma.enums import DataSourceType
from prisma.models import (
    Business,
    DataSource,
    DataSourceTableColumn,
    DataSourceTableDescription,
    User,
)
from prisma.types import DataSourceTableColumnCreateInput

# Imports the schema and metadata from the snowflake database to the
# local database.

SKIP_COLUMNS = [
    # fivetran columns
    "^_FIVETRAN_",
    # airbyte columns
    "^_AIRBYTE_",
    "_SCD$",
    # TODO these keywords cause issues with snowflake SQL, so we are excluding them
    # (?i) for inline regexhttps://stackoverflow.com/questions/500864/case-insensitive-regular-expression-without-re-compile
    "(?i)default",
    "(?i)values",
]

SKIP_TABLES = ["FIVETRAN_AUDIT", "^_AIRBYTE_", "_SCD$"]


# TODO source this from the ENV?
THREAD_POOL_SIZE = 20


"""
Imports the schema and metadata from the snowflake database to the
local database.
"""
import typing as t

import query_runner

SnowflakeColumnDescription = t.TypedDict(
    "SnowflakeColumnDescription",
    {
        "check": None,
        "comment": None,
        "default": None,
        "expression": None,
        "kind": str,
        "name": str,
        "null?": str,
        "policy name": None,
        "primary key": str,
        "type": str,
        "unique key": str,
    },
)

# TODO right now we are married to snowflake, but we'll need to be flexible with the type definitions from other systems in the future
class SnowflakeTableDescription(t.TypedDict):
    automatic_clustering: str
    bytes: int
    change_tracking: str
    cluster_by: str
    comment: str
    created_on: str
    database_name: str
    is_external: str
    kind: str
    name: str
    owner: str
    retention_time: str
    rows: int
    schema_name: str


def fqn_from_table_description(description: SnowflakeTableDescription) -> str:
    return f"{description['database_name']}.{description['schema_name']}.{description['name']}"


class Import:
    def __init__(self, user_id: int, data_source_id: int, table_limit: int, column_limit: int, column_value_limit: int):
        self.column_pool = ThreadPool(processes=THREAD_POOL_SIZE)
        self.limits = {"table": table_limit, "column": column_limit, "column_value": column_value_limit}

        log.debug("starting import", data_source_id=data_source_id, user_id=user_id)

        self.db = utils.db.application_database_connection()

        # TODO should create helper for this, find first + throw
        user = self.db.user.find_unique(
            where={"id": int(user_id)}, include={"business": {"include": {"dataSources": True}}}
        )
        if user is None:
            raise Exception("User not found")

        data_source = user.business.dataSources[0]

        self.embedding_builder = EmbeddingBuilder(data_source)

        self.create_table_records(data_source)

        # Save embedding indexes to the file system, this must be done in one fell swoop due to how the
        # embeddings indexes are generated.
        self.embedding_builder.save()

    def create_table_records(self, data_source: DataSource) -> None:
        # TODO this will create a new cursor each time, we should use a single cursor for this script
        table_list = query_runner.run_query(
            data_source_id=data_source.id,
            sql=f"SHOW TABLES LIMIT {self.limits['table'] or 1000}",
            disable_query_protections=True,
        )

        # TODO add return type to run_query, this can be done with generics in python
        table_list = t.cast(t.List[SnowflakeTableDescription], table_list)

        log.info("inspecting tables", table_count=len(table_list))

        for table in table_list:
            if any(re.search(regex, table["name"]) for regex in SKIP_TABLES):
                log.debug("skipping table", table=table)
            else:
                self.create_table_record(data_source, table)

    def create_table_record(self, data_source: DataSource, table: SnowflakeTableDescription):
        fqn = fqn_from_table_description(table)
        log.debug("creating local table record", fqn=fqn)

        # TODO why can't pyright determine the right types here? It's clearly a str, number | string dict?
        table_locator = {"dataSourceId": data_source.id, "fullyQualifiedName": fqn}

        # Still can't believe you can't unique query on a compound index in prisma!
        table_description = self.db.datasourcetabledescription.find_first(where=table_locator)

        if not table_description:
            table_description = self.db.datasourcetabledescription.create(data=table_locator)

        self.create_column_records(data_source, table_description)

        self.embedding_builder.add_table(
            fqn, column_limit=self.limits["column"], column_value_limit=self.limits["column_value"]
        )

    def create_column_records(self, data_source: DataSource, table_description: DataSourceTableDescription):
        row_count = self.get_total_rows(data_source, table_description)

        raw_column_list = query_runner.run_query(
            data_source.id,
            f"""
            DESCRIBE TABLE {sql.normalize_fqn_quoting(table_description.fullyQualifiedName)}
            """,
            disable_query_protections=True,
        )

        log.info(
            "inspecting columns",
            table_name=sql.unqualified_table_name(table_description.fullyQualifiedName),
            full_count=len(raw_column_list),
            limit=self.limits["column"],
        )

        breakpoint()

        futures = [
            self.column_pool.apply_async(
                self.create_column_record, args=(data_source, table_description, column, row_count)
            )
            # result is not important, otherwise we would `async_task.get()`
            for column in raw_column_list[0 : self.limits["column"]]
        ]

        # TODO what is the default timeout of `get`?
        # Wait for futures to finish
        [future.get() for future in futures]

    def get_total_rows(self, data_source: DataSource, table_description: DataSourceTableDescription) -> int:
        raw_sql = f"""
        SELECT COUNT(*) as count
        FROM {sql.normalize_fqn_quoting(table_description.fullyQualifiedName)}
        """

        counts = query_runner.run_query(
            data_source.id,
            raw_sql,
            disable_query_protections=True,
        )

        # TODO this will throw an error if there's an upstream issue, which is what we want for now
        return counts[0]["COUNT"]

    def create_column_record(
        self,
        data_source: DataSource,
        table_description: DataSourceTableDescription,
        column: SnowflakeColumnDescription,
        row_count: int,
    ) -> None:
        name = column["name"]
        type = column["type"]

        if any(re.search(regex, name) for regex in SKIP_COLUMNS):
            log.debug("skipping column", column=name)
            return

        log.info(
            "inspecting column",
            table_name=unqualified_table_name(table_description.fullyQualifiedName),
            name=name,
            type=type,
            column=name,
        )

        # since we are in a thread pool, we want to use a unique cursor to avoid any state issues
        # by default the query runner uses a unique cursor per query

        distinct_row_count = self.get_unique_row_count(data_source, table_description, name)

        column_external_id_locator = {"dataSourceTableDescriptionId": table_description.id, "name": name}

        column_description_payload: DataSourceTableColumnCreateInput = column_external_id_locator | {
            "dataSourceId": data_source.id,
            "type": column["type"],
            "kind": column["kind"],
            "isNull": column["null?"] == "Y",
            "default": column["default"],
            "distinctRows": distinct_row_count,
            # TODO ideally, this should not be passed here and already added upstream
            "rows": row_count,
            "extendedProperties": json.dumps(
                # TODO are there any other properties from snowflake?
                {
                    "comment": column["comment"],
                }
            ),
            "embeddingsCache": "{}",
        }

        # TODO I hope we can use upsert here instead...
        table_column = self.db.datasourcetablecolumn.find_first(where=column_external_id_locator)

        if table_column:
            log.debug("updating column record", column=name)
            self.db.datasourcetablecolumn.update(data=column_description_payload, where={"id": table_column.id})
        else:
            self.db.datasourcetablecolumn.create(data=column_description_payload)

    def get_unique_row_count(
        self, data_source: DataSource, table_description: DataSourceTableDescription, column_name: str
    ):
        raw_sql = f"""
        SELECT COUNT(DISTINCT({sql.normalize_fqn_quoting(table_description.fullyQualifiedName)}.{sql.normalize_fqn_quoting(name)})) as count
        FROM {sql.normalize_fqn_quoting(table_description.fullyQualifiedName)}
        """

        # Gets the distinct rows for the column and the total rows
        counts = query_runner.run_query(
            data_source.id,
            raw_sql,
            disable_query_protections=True,
        )

        # TODO we should assert against there being a single return value here
        for count in counts:
            distinct_row_count = count["COUNT"]
            break

        return distinct_row_count


# TODO move this to a single command.py
@click.command()
@click.option("--user-id", type=int, required=True)
@click.option("--data-source-id", type=int, required=True)
@click.option("--table-limit", type=int)
@click.option("--column-limit", type=int)
@click.option("--column-value-limit", type=int)
def cli(**kwargs):
    Import(**kwargs)


if __name__ == "__main__":
    cli()
