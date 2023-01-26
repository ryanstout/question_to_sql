# Called from import.py, builds and updates the embedding indexes

import collections
import math
import re
from multiprocessing.pool import ThreadPool

from prisma.models import (
    Business,
    DataSource,
    DataSourceTableColumn,
    DataSourceTableDescription,
    User,
)

import python.utils.sql as sql
from python.embeddings.ann_index import AnnIndex
from python.utils.connections import Connections
from python.utils.entropy import token_entropy
from python.utils.logging import log

# How long of a value do we create an embedding for?
# embeddings have a window, so we truncate the values to fit into the window
# TODO where are these limits documented in openai?
MAX_VALUE_LENGTH = 600
MAX_FOR_SMALL_VALUE = 100

# max length is 8191 tokens, but we'll keep it below for now so we don't have to count tokens
MAX_EMBEDDING_TOKENS = 7500
TOKEN_ENTROPY_THRESHOLD = 2.0  # Anything less and this is probably a GUID or similar


def in_groups_of(l, n):

    # looping till length l
    for i in range(0, len(l), n):
        yield l[i : i + n]


class EmbeddingBuilder:
    def __init__(self, datasource: DataSource):
        # TODO these two should be pulled from the input datasource
        self.connection = Connections()

        self.db = self.connection.open()

        self.datasource = datasource

        # See docs/prompt_embeddings.md for info on index types

        # Table indexes
        self.idx_table_names = AnnIndex(self.db, 0, f"python/indexes/{datasource.id}/table_names")
        self.idx_column_names = AnnIndex(self.db, 1, f"python/indexes/{datasource.id}/column_names")
        self.idx_table_and_column_names = AnnIndex(self.db, 3, f"python/indexes/{datasource.id}/table_and_column_names")

        # Table and Columns indexes
        self.idx_table_and_column_names_and_values = AnnIndex(self.db, 4, f"python/indexes/{datasource.id}/table_and_column_names_and_values")
        self.idx_column_name_and_all_column_values = AnnIndex(self.db, 5, f"python/indexes/{datasource.id}/column_name_and_all_column_values")

        # Cell Values
        self.idx_values = AnnIndex(self.db, 2, f"python/indexes/{datasource.id}/values")

        # Temp store for all short string values in a table
        # TODO: this will blow up on huge tables
        self.table_values = []

    def add_table(self, name: str, column_limit: int, column_value_limit: int) -> None:
        table = self.db.datasourcetabledescription.find_first(where={"fullyQualifiedName": name, "dataSourceId": self.datasource.id})

        if table is None:
            raise Exception(f"Table {name} not found")

        # TODO we should be doing upsert instead

        self.idx_table_names.add(self.datasource.id, name, table.id, None, None)

        all_columns = self.db.datasourcetablecolumn.find_many(where={"dataSourceTableDescriptionId": table.id})

        log.debug("generating embedding for table", table_name=name, total_columns=len(all_columns), limit=column_value_limit)

        columns = all_columns[0:column_limit]

        column_add_pool = ThreadPool(processes=20)

        # not all column names will be included in the index, depending on the token size
        column_names = []

        # run all of the embedding results async and wait for them all to complete
        column_add_results = []

        for column in columns:
            # TODO we should be doing upsert instead

            column_names.append(column.name)
            # Add individual column names
            self.idx_column_names.add(self.datasource.id, column.name, table.id, column.id, None)

            # TODO here we are deciding which columns should be put into the vector index,
            #      right now, we are just using the distict count of the column to decide
            #      but long term, we'd want a more complex heuristic
            # Add cell values (requires a full scan of each table)
            if column.distinctRows < column_value_limit:
                column_add_results.append(column_add_pool.apply_async(self.add_table_column_values, (table, column, column_value_limit)))
                # self.add_table_column_values(table, column, column_value_limit=column_value_limit)
            else:
                log.debug("not indexing column, too many values", column_name=column.name, distinct_rows=column.distinctRows)

        log.debug("waiting for async results")

        # wait sync for all AsyncResults to complete
        for result in column_add_results:
            # try:
            result.get()
            # except ValueError:
            #     # TODO: should probably fail fully and we can figure it out
            #     log.error("async result timed out")

        log.debug("async results complete", total=len(column_add_results), successful=len([r for r in column_add_results if r.successful()]))

        # Add table and column names as a single string (for table lookup)
        self.idx_table_and_column_names.add(self.datasource.id, name + " " + " ".join(column_names), table.id, None, None)

        # Add for table + column names + all values
        for table_value_group in in_groups_of("\n".join(self.table_values), MAX_EMBEDDING_TOKENS):
            full_table_str = name + "\n" + "\n".join(column_names) + "\n" + table_value_group
            self.idx_column_name_and_all_column_values.add(self.datasource.id, full_table_str, table.id, None, None)

    def add_table_column_values(self, table: DataSourceTableDescription, column: DataSourceTableColumn, column_value_limit: int):
        # only index string columns
        if not re.search("^VARCHAR", column.type):
            log.debug("skipping embeddings for column, not varchar", column_name=column.name)
            return

        snowflake_cursor = self.connection.snowflake_cursor()

        # Get all the values for this column
        values = snowflake_cursor.execute(
            f"""
            SELECT {column.name} as VALUE, COUNT(*) AS COUNT
            FROM {sql.normalize_fqn_quoting(table.fullyQualifiedName)}
            WHERE {column.name} IS NOT NULL
            GROUP BY {column.name}
            ORDER BY COUNT DESC
            LIMIT {column_value_limit}
            """
        )

        column_values = []

        # Add each value to the index
        for value in values:
            value_str = value["VALUE"]

            # TODO we could break the input into chunks and generate embedding for each chunk
            if not value_str or len(value_str) >= MAX_VALUE_LENGTH:
                log.debug("skipping embedding, too long")
                continue

            entropy = token_entropy(value_str)
            if entropy <= TOKEN_ENTROPY_THRESHOLD:
                log.debug("skipping embedding, not enough entropy", entropy=entropy)
                continue

            log.debug("adding embedding", table_name=table.fullyQualifiedName.split(".")[-1], column_name=column.name, entropy=entropy)

            # We have 5 different indexes we are building (tables, columns, column values, etc)
            # For larger indexes, we track shorter column values. Check out `docs/prompt_embeddings.md` for more
            if len(value_str) < MAX_FOR_SMALL_VALUE:
                log.debug("skipping embedding, too long for small value")

                self.table_values.append(value_str)
                column_values.append(value_str)

            self.idx_values.add(self.datasource.id, value_str, table.id, column.id, value_str)

        # Add for column name + all column values (keeping below max embedding)
        for col_value_group in in_groups_of("\n".join(column_values), MAX_EMBEDDING_TOKENS):
            full_column_str = column.name + "\n" + col_value_group
            self.idx_column_name_and_all_column_values.add(self.datasource.id, full_column_str, table.id, column.id, None)

    # this is an expensive operation, do this as minimially as we can!
    def save(self):
        # Write out the indexes
        self.idx_table_names.save()
        self.idx_column_names.save()
        self.idx_table_and_column_names.save()
        self.idx_table_and_column_names_and_values.save()
        self.idx_column_name_and_all_column_values.save()
        self.idx_values.save()
