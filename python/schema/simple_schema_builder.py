"""
The SqlInspector takes a simple version of the schema consisting of a dict of lists of strings (SimpleSchema type)

This is needed to resolve the table and column names.


"""

from python import utils
from python.sql.types import SimpleSchema
from python.utils.sql import unqualified_table_name

from prisma import Prisma


class SimpleSchemaBuilder:
    def __init__(self):
        self.schema: SimpleSchema = {}

    def build(self, db: Prisma, data_source_id: int) -> SimpleSchema:
        """
        Generate the SimpleSchema for a given data source id
        """

        data_source = db.datasource.find_first(where={"id": data_source_id})

        if not data_source:
            raise ValueError(f"Data Source {data_source_id} not found")

        for table in db.datasourcetabledescription.find_many(where={"dataSourceId": data_source_id}):
            fqn = table.fullyQualifiedName
            table_name = unqualified_table_name(fqn).lower()
            self.schema[table_name] = []

            for column in db.datasourcetablecolumn.find_many(where={"dataSourceTableDescriptionId": table.id}):
                self.schema[table_name].append(column.name.lower())

        return self.schema
