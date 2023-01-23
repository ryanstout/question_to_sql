# Called from import.py, builds and updates the embedding indexes

import re
from prisma.models import User, DataSource, Business, DataSourceTableDescription, DataSourceTableColumn
import collections
import math
from utils.entropy import token_entropy

from embeddings.ann_index import AnnIndex

# How long of a value do we create an embedding for?
MAX_VALUE_LENGTH = 600
MAX_FOR_SMALL_VALUE = 100
# max length is 8191 tokens, but we'll keep it below for now so we don't have to count tokens
MAX_EMBEDDING_TOKENS = 7500
TOKEN_ENTROPY_THRESHOLD = 2.0  # Anything less and this is probably a GUID or similar


def in_groups_of(l, n):

    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]


class EmbeddingBuilder:
    def __init__(self, prisma_db, snowflake_cursor, datasource: DataSource):
        self.db = prisma_db
        self.snowflake_cursor = snowflake_cursor
        self.datasource = datasource

        # See docs/prompt_embeddings.md for info on index types

        # Table indexes
        self.idx_table_names = AnnIndex(
            self.db, 0, 'python/indexes/table_names')
        self.idx_column_names = AnnIndex(
            self.db, 1, 'python/indexes/column_names')
        self.idx_table_and_column_names = AnnIndex(
            self.db, 3, 'python/indexes/table_and_column_names')

        # Table and Columns indexes
        self.idx_table_and_column_names_and_values = AnnIndex(
            self.db, 4, 'python/indexes/table_and_column_names_and_values')
        self.idx_column_name_and_all_column_values = AnnIndex(
            self.db, 5, 'python/indexes/column_name_and_all_column_values')

        # Cell Values
        self.idx_values = AnnIndex(self.db, 2, 'python/indexes/values')

        # Temp store for all short string values in a table
        # TODO: this will blow up on huge tables
        self.table_values = []

    def add_table(self, name: str):
        # Find table in db
        table = self.db.datasourcetabledescription.find_first(where={
            'fullyQualifiedName': name,
            'dataSourceId': self.datasource.id
        })

        if table is None:
            raise Exception(f"Table {name} not found")

        # Clear embedding links for table
        self.db.embeddinglink.delete_many(
            where={'tableId': table.id})

        # Table name
        self.idx_table_names.add(name, table.id, None, None)

        # Column Names
        columns = self.db.datasourcetablecolumn.find_many(where={
            'dataSourceTableDescriptionId': table.id
        })

        column_names = []
        for column in columns:
            # Clear embedding links for table
            self.db.embeddinglink.delete_many(
                where={'columnId': column.id})

            column_names.append(column.name)
            # Add individual column names
            self.idx_column_names.add(column.name, table.id, column.id, None)

            # Add cell values (requires a full scan of each table)
            if column.distinctRows < 1000:
                self.add_table_column_values(table, column)

        # Add table and column names as a single string (for table lookup)
        self.idx_table_and_column_names.add(
            name + ' ' + ' '.join(column_names), table.id, None, None)

        # Add for table + column names + all values
        for table_value_group in in_groups_of("\n".join(self.table_values), MAX_EMBEDDING_TOKENS):
            full_table_str = name + "\n" + \
                "\n".join(column_names) + "\n" + table_value_group
            self.idx_column_name_and_all_column_values.add(
                full_table_str, table.id, None, None)

    def add_table_column_values(self, table: DataSourceTableDescription, column: DataSourceTableColumn):
        if re.search("^(VARCHAR|VARIANT)", column.type):
            # Get all the values for this column
            values = self.snowflake_cursor.execute(
                f"select DISTINCT({column.name}) as value from {table.fullyQualifiedName} LIMIT 50;")

            column_values = []

            # Add each value to the index
            for (value) in values:
                value_str = value['VALUE']
                # none check, limit embeddings to shorter values
                if value_str and len(value_str) < MAX_VALUE_LENGTH:
                    entropy = token_entropy(value_str)

                    if entropy > TOKEN_ENTROPY_THRESHOLD:
                        print('value: ', column.name, value_str, entropy)

                        # Track shorter values for full indexes
                        if len(value_str) < MAX_FOR_SMALL_VALUE:
                            self.table_values.append(value_str)
                            column_values.append(value_str)
                        self.idx_values.add(value_str, table.id,
                                            column.id, value_str)

            # Add for column name + all column values (keeping below max embedding)
            for col_value_group in in_groups_of("\n".join(column_values), MAX_EMBEDDING_TOKENS):
                full_column_str = column.name + "\n" + col_value_group
                self.idx_column_name_and_all_column_values.add(
                    full_column_str, table.id, column.id, None)

    def save(self):
        # Write out the indexes
        self.idx_table_names.save()
        self.idx_column_names.save()
        self.idx_table_and_column_names.save()
        self.idx_table_and_column_names_and_values.save()
        self.idx_column_name_and_all_column_values.save()
        self.idx_values.save()
