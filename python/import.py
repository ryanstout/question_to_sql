from python.setup import log

import faulthandler
import json
import re
from multiprocessing.pool import ThreadPool

import click
import snowflake.connector
from decouple import config
from prisma.enums import DataSourceType
from prisma.models import (
    Business,
    DataSource,
    DataSourceTableColumn,
    DataSourceTableDescription,
    User,
)
from snowflake.connector.cursor import DictCursor

import python.utils.sql as sql
from prisma import Prisma
from python.embeddings.embedding_builder import EmbeddingBuilder
from python.utils.connections import Connections
from python.utils.logging import log

# Imports the schema and metadata from the snowflake database to the
# local database.


# Setup the fault handler so we can send SIGABRT and get a stack trace
faulthandler.enable()


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


THREAD_POOL_SIZE = 20


class Import:
    def __init__(self, user_id, database_name, table_limit, column_limit, column_value_limit):
        self.column_pool = ThreadPool(processes=THREAD_POOL_SIZE)
        self.connections = Connections()
        self.connections.open()

        self.limits = {"table": table_limit, "column": column_limit, "column_value": column_value_limit}

        log.debug("starting import", database=database_name, user_id=user_id)

        try:
            self.db = self.connections.db

            user = self.db.user.find_unique(where={"id": int(user_id)}, include={"business": True})
            if user is None:
                raise Exception("User not found")

            business = self.find_or_create_business(user)
            datasource = self.find_or_create_datasource(business)

            # Dump the data from each table into the database
            self.snowflake_cursor = self.connections.snowflake_cursor()

            self.embedding_builder = EmbeddingBuilder(datasource)

            # TODO pull this from the user credentials
            self.snowflake_cursor.execute("use warehouse COMPUTE_WH;")

            self.create_table_records(datasource, database_name, limit=table_limit)

            # Save embedding indexes to the file system
            self.embedding_builder.save()

        finally:
            self.connections.close()

    def create_table_records(self, data_source: DataSource, database_name: str, limit: int) -> None:
        # TODO add dict to represent this
        rawTableList = self.snowflake_cursor.execute("SHOW TABLES IN DATABASE " + database_name)

        tableList = list(rawTableList)

        log.debug("inspecting tables", full_count=len(tableList), limit=limit)

        for table in list(tableList)[0:limit]:
            if any(re.search(regex, table["name"]) for regex in SKIP_TABLES):
                log.debug("skipping table", table=table)
            else:
                self.create_table_record(data_source, table)

    def create_table_record(self, datasource: DataSource, table):
        # TODO this should be moved to a dedicated method
        fqn = f"{table['database_name']}.{table['schema_name']}.{table['name']}"
        log.debug("creating table record", fqn=fqn)

        table_locator = {"dataSourceId": datasource.id, "fullyQualifiedName": fqn}

        # Still can't believe you can't unique query on a compound index in prisma.
        table_description = self.db.datasourcetabledescription.find_first(where=table_locator)

        description_payload = table_locator | {
            "skip": False,
            "generatedSQLCache": "",
            "embeddingsCache": "{}",
        }

        if table_description:
            table_description = self.db.datasourcetabledescription.update(data=description_payload, where={"id": table_description.id})
        else:
            table_description = self.db.datasourcetabledescription.create(data=description_payload)

        self.create_column_records(table_description, limit=self.limits["column"])
        self.embedding_builder.add_table(fqn, column_limit=self.limits["column"], column_value_limit=self.limits["column_value"])

    def create_column_records(self, table_description: DataSourceTableDescription, limit: int):
        cursor = self.snowflake_cursor
        row_count = self.get_total_rows(table_description, cursor)

        raw_column_list = cursor.execute(
            f"""
            DESCRIBE TABLE {sql.normalize_fqn_quoting(table_description.fullyQualifiedName)}
            """
        ).fetchall()

        log.debug("inspecting columns", table_name=table_description.fullyQualifiedName, full_count=len(raw_column_list), limit=limit)

        column_list = raw_column_list[0:limit]

        futures = []
        for column in column_list:
            futures.append(self.column_pool.apply_async(self.create_column_record, args=(table_description, column, row_count)))
            # result is not important, otherwise we would `async_task.get()`

        # Wait for futures to finsish
        [future.get() for future in futures]

    def create_column_record(self, table_description: DataSourceTableDescription, column, row_count: int) -> None:
        name = column["name"]
        type = column["type"]

        if any(re.search(regex, name) for regex in SKIP_COLUMNS):
            log.debug("skipping column", column=name)
            return

        log.info("inspecting column", table_name=table_description.fullyQualifiedName, name=name, type=type, column=name)

        # since we are in a thread pool, we want to use a unique cursor to avoid any state issues
        cursor = self.connections.snowflake_cursor()

        # Get the cardinality of the column
        distinct_row_count = self.get_cardinality(table_description, cursor, name)

        column_external_id_locator = {"dataSourceTableDescriptionId": table_description.id, "name": name}

        column_description_payload = column_external_id_locator | {
            "type": column["type"],
            "kind": column["kind"],
            "skip": False,
            "inspectionMetadata": "{}",
            "isNull": column["null?"] == "Y",
            "default": column["default"] or "",
            "distinctRows": distinct_row_count,
            # TODO ideally, this should not be passed here and already added upstream
            "rows": row_count,
            "extendedProperties": json.dumps(
                {
                    "comment": column["comment"],
                }
            ),
            "embeddingsCache": "{}",
        }

        # TODO I hope we can use upsert here instead...
        table_column = self.db.datasourcetablecolumn.find_first(where=column_external_id_locator)

        if table_column:
            self.db.datasourcetablecolumn.update(data=column_description_payload, where={"id": table_column.id})
        else:
            self.db.datasourcetablecolumn.create(data=column_description_payload)

    def get_cardinality(self, table_description, cursor, name):
        # Gets the distinct rows for the column and the total rows
        counts = cursor.execute(
            f"""
            SELECT COUNT(DISTINCT({sql.normalize_fqn_quoting(table_description.fullyQualifiedName)}.{sql.normalize_fqn_quoting(name)})) as count
            FROM {sql.normalize_fqn_quoting(table_description.fullyQualifiedName)}
            """
        )

        # TODO we should assert against there being a single return value here
        for count in counts:
            distinct_row_count = count["COUNT"]
            break

        return distinct_row_count

    def get_total_rows(self, table_description, cursor):
        raw_sql = f"""
            SELECT COUNT(*) as count
            FROM {sql.normalize_fqn_quoting(table_description.fullyQualifiedName)}
            """

        counts = cursor.execute(raw_sql)

        for count in counts:
            row_count = count["COUNT"]
            break

        return row_count

    def find_or_create_business(self, user):
        # Create and assign a business if there isn't one
        if user.business is None:
            business = self.db.business.create(data={"name": config("SNOWFLAKE_DATABASE")})
            self.db.user.update(data={"businessId": business.id}, where={"id": user.id})

            return business
        else:
            return user.business

    # TODO temp method to create a datasource, should be read-only from the DB
    def find_or_create_datasource(self, business: Business):
        first_source = self.db.datasource.find_first(where={"businessId": business.id})

        if first_source is not None:
            return first_source

        db_name = config("SNOWFLAKE_DATABASE")
        return self.db.datasource.create(
            data={
                "name": f"Snowflake for {db_name}",
                "businessId": int(business.id),
                "credentials": "{}",
                "type": DataSourceType.SNOWFLAKE,
            }
        )


@click.command()
@click.option("--user-id", type=int)
@click.option("--database-name", type=str)
@click.option("--table-limit", type=int)
@click.option("--column-limit", type=int)
@click.option("--column-value-limit", type=int)
def cli(**kwargs):
    Import(**kwargs)


if __name__ == "__main__":
    cli()
