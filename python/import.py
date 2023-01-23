# Imports the schema and metadata from the snowflake database to the
# local database.

import re
from snowflake.connector.cursor import DictCursor
import snowflake.connector
from decouple import config
import sys
from prisma import Prisma
from prisma.models import User, DataSource, Business, DataSourceTableDescription, DataSourceTableColumn
from prisma.enums import DataSourceType
import json

from embeddings.embedding_builder import EmbeddingBuilder
from utils.connections import Connections


class Import():
    def __init__(self, user_id, database):
        self.connections = Connections()
        self.connections.open()

        try:
            self.db = self.connections.db

            user = self.db.user.find_unique(
                where={'id': int(user_id)},
                include={'business': True})
            if user is None:
                raise Exception("User not found")

            business = self.find_or_create_business(user)
            datasource = self.find_or_create_datasource(business)

            # Dump the data from each table into the database
            self.snowflake_cursor = self.connections.snowflake_cursor()

            self.embedding_builder = EmbeddingBuilder(
                self.db, self.snowflake_cursor, datasource)

            # Use the only warehouse for now
            self.snowflake_cursor.execute('use warehouse COMPUTE_WH;')

            tableList = self.snowflake_cursor.execute(
                "SHOW TABLES IN DATABASE " + database)

            # from IPython import embed; embed()

            for table in tableList:
                name = table['name']

                # Filter out airbyte tables
                if not (re.search("^_AIRBYTE_", name) or re.search("_SCD$", name)):
                    self.create_table_record(datasource, table)

            # Save embedding indexes
            self.embedding_builder.save()

        finally:
            self.connections.close()

    def create_table_record(self, datasource: DataSource, table):
        fqn = f"{table['database_name']}.{table['schema_name']}.{table['name']}"
        print("\n", fqn)

        # Still can't believe you can't unique query on a compound index in prisma.
        table_description = self.db.datasourcetabledescription.find_first(
            where={
                'dataSourceId': datasource.id,
                'fullyQualifiedName': fqn
            })

        if table_description:
            table_description = self.db.datasourcetabledescription.update(data={
                'dataSourceId': datasource.id,
                'skip': False,
                'fullyQualifiedName': fqn,
                'generatedSQLCache': '',
                'embeddingsCache': '{}',
            }, where={
                'id': table_description.id
            })
        else:
            table_description = self.db.datasourcetabledescription.create(data={
                'dataSourceId': datasource.id,
                'skip': False,
                'fullyQualifiedName': fqn,
                'generatedSQLCache': '',
                'embeddingsCache': '{}',
            })

        self.create_column_records(table_description)
        self.embedding_builder.add_table(fqn)

    def create_column_records(self, table_description: DataSourceTableDescription):
        cursor = self.snowflake_cursor
        row_count = self.get_total_rows(table_description, cursor)

        columnInfo = cursor.execute(
            f"DESCRIBE TABLE {table_description.fullyQualifiedName}")

        for column in columnInfo:
            name = column['name']
            if not (re.search("^_AIRBYTE_", name) or name.lower() == 'default' or name.lower() == 'values'):
                kind = column['kind']
                type = column['type']

                print(f"> {name}, {type}")
                # Get the cardinality of the column
                distinct_row_count = self.get_cardinality(
                    table_description, cursor, name)

                table_column = self.db.datasourcetablecolumn.find_first(
                    where={
                        'dataSourceTableDescriptionId': table_description.id,
                        'name': name
                    })

                data = {
                    'dataSourceTableDescriptionId': table_description.id,
                    'name': column['name'],
                    'type': column['type'],
                    'kind': column['kind'],
                    'skip': False,
                    'inspectionMetadata': '{}',
                    'isNull': column['null?'] == 'Y',
                    'default': column['default'] or '',
                    'distinctRows': distinct_row_count,
                    'rows': row_count,

                    'extendedProperties': json.dumps({
                        'comment': column['comment'],
                    }),
                    'embeddingsCache': '{}',
                }

                if table_column:
                    self.db.datasourcetablecolumn.update(data=data, where={
                        'id': table_column.id
                    })
                else:
                    table_column = self.db.datasourcetablecolumn.create(
                        data=data)

    def get_cardinality(self, table_description, cursor, name):
        # Gets the distinct rows for the column and the total rows
        counts = cursor.execute(
            f"SELECT COUNT(DISTINCT({table_description.fullyQualifiedName}.{name})) as count FROM {table_description.fullyQualifiedName};")
        for count in counts:
            distinct_row_count = count['COUNT']
            break
        return distinct_row_count

    def get_total_rows(self, table_description, cursor):
        counts = cursor.execute(
            f"SELECT COUNT(*) as count FROM {table_description.fullyQualifiedName}")
        for count in counts:
            row_count = count['COUNT']
            break
        return row_count

    def find_or_create_business(self, user):
        # Create and assign a business if there isn't one
        if user.business is None:
            business = self.db.business.create(data={
                'name': config("SNOWFLAKE_DATABASE")
            })
            self.db.user.update(
                data={'businessId': business.id}, where={'id': user.id})

            return business
        else:
            return user.business

    def find_or_create_datasource(self, business: Business):
        # Temp method to create a datasource
        first_source = self.db.datasource.find_first(
            where={'businessId': business.id})

        if first_source is not None:
            return first_source

        db_name = config("SNOWFLAKE_DATABASE")
        return self.db.datasource.create(data={
            'name': f"Snowflake for {db_name}",
            'businessId': int(business.id),
            'credentials': '{}',
            'type': DataSourceType.SNOWFLAKE,
        })


if __name__ == "__main__":
    Import(sys.argv[1], config("SNOWFLAKE_DATABASE"))
