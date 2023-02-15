from python.setup import log

import json
import re
import typing as t
from multiprocessing.pool import ThreadPool

import query_runner
import utils

import python.utils.sql as sql
from python.embeddings.embedding_builder import EmbeddingBuilder

from prisma.models import DataSource, DataSourceTableDescription
from prisma.types import DataSourceTableColumnCreateInput

# Imports the schema, and schema, metadata from the snowflake database to the local database.
# on the SQL side, this mostly performs a bunch of describes & COUNTs

SKIP_COLUMNS = [
    # some end with one `_`, some with two
    "^__HEVO_",
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


# TODO easier to define a high limit than remove `LIMIT`s in SQL`
MAX_LIMIT = 10_000


class Importer:
    def __init__(self, data_source_id: int, table_limit: int, column_limit: int, column_value_limit: int):
        self.column_pool = ThreadPool(processes=THREAD_POOL_SIZE)
        self.limits = {
            "table": table_limit or MAX_LIMIT,
            "column": column_limit or MAX_LIMIT,
            "column_value": column_value_limit or MAX_LIMIT,
        }

        # TODO maybe move to a file-global variable vs a class variable
        self.db = utils.db.application_database_connection()

        log.debug("starting import", data_source_id=data_source_id)

        # TODO should create helper for this, find first + throw like we have in JS
        data_source = self.db.datasource.find_unique(where={"id": int(data_source_id)})
        if data_source is None:
            raise Exception("data source not found")

        self.embedding_builder = EmbeddingBuilder(data_source)

        self.create_table_records(data_source)

        # Save embedding indexes to the file system, this must be done in one fell swoop due to how the
        # embeddings indexes are generated. This cannot be done incrementally.
        self.embedding_builder.write_indexes_to_disk()

    def create_table_records(self, data_source: DataSource) -> None:
        # TODO this will create a new cursor each time, we should use a single cursor for this script
        table_list = query_runner.run_query(
            data_source_id=data_source.id,
            sql=f"SHOW TABLES LIMIT {self.limits['table']}",
            disable_query_protections=True,
        )

        # TODO so terrible, refact when we settled on a functional lib
        tables_with_content = []
        for table in table_list:
            if table["rows"] == 0:
                log.debug("skipping table with no rows", table=table["name"])
                continue
            tables_with_content.append(table)

        # sorts in place, ascending
        # start with the smallest table first (cheapest to query) in case something goes wrong
        tables_with_content.sort(key=lambda x: x["rows"] or 0)

        # TODO add return type to run_query, this can be done with generics in python
        tables_with_content = t.cast(list[SnowflakeTableDescription], tables_with_content)

        log.info("inspecting tables", table_count=len(tables_with_content))

        for table in tables_with_content:
            # TODO this is really confusing syntax, if we can land on a functional lib for python we should replace this
            if any(re.search(regex, table["name"]) for regex in SKIP_TABLES):
                log.debug("skipping table", table=table)
            else:
                self.create_table_record(data_source, table)

    def create_table_record(self, data_source: DataSource, table: SnowflakeTableDescription):
        fqn = fqn_from_table_description(table)
        log.debug("creating local table record", fqn=fqn)

        # TODO why can't pyright determine the right types here? It's clearly a str, number | string dict?
        table_locator = dict(
            {
                "dataSourceId": data_source.id,
                "fullyQualifiedName": fqn,
            }
        )

        # Still can't believe you can't unique query on a compound index in prisma!
        table_description = self.db.datasourcetabledescription.find_first(where=table_locator)

        if not table_description:
            table_description = self.db.datasourcetabledescription.create(data=table_locator)

        self.create_column_records(data_source, table_description)

        # this is an expensive operation, does a full table scan for each column in
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

    # TODO a better approach here would be to use the INFORMATION_SCHEMA of the database to get the row count
    def get_total_rows(self, data_source: DataSource, table_description: DataSourceTableDescription) -> int:
        raw_sql = f"""
        SELECT COUNT(*) as COUNT
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
            table_name=sql.unqualified_table_name(table_description.fullyQualifiedName),
            name=name,
            type=type,
            column=name,
        )

        # since we are in a thread pool, we want to use a unique cursor to avoid any state issues
        # by default the query runner uses a unique cursor per query

        distinct_row_count = self.get_unique_row_count(data_source, table_description, name)

        column_external_id_locator = {"dataSourceTableDescriptionId": table_description.id, "name": name}

        # TODO pyright does not like merging dicts and typing, need to fix
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
        # TODO I imagine this has to do a full table scan as well, we should try to figure ouw how much these queries cost
        raw_sql = f"""
        SELECT COUNT(DISTINCT({sql.normalize_fqn_quoting(table_description.fullyQualifiedName)}.{sql.normalize_fqn_quoting(column_name)})) as count
        FROM {sql.normalize_fqn_quoting(table_description.fullyQualifiedName)}
        """

        # Gets the distinct rows for the column and the total rows
        counts = query_runner.run_query(
            data_source.id,
            raw_sql,
            disable_query_protections=True,
        )

        # TODO this will break if the upstream breaks, this is intentional for now
        return counts[0]["COUNT"]
