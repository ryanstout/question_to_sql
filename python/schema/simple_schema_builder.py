"""
The SqlInspector takes a simple version of the schema consisting of a dict of lists of strings (SimpleSchema type)

This is needed to resolve the table and column names.
"""

import python.utils.db
from python.sql.types import SimpleSchema
from python.utils.sql import unqualified_table_name

db = python.utils.db.application_database_connection()


def build_simple_schema(data_source_id: int) -> SimpleSchema:
    """
    Generate the SimpleSchema for a given data source id. Assumes data source ID is valid
    """

    schema: SimpleSchema = {}

    for table in db.datasourcetabledescription.find_many(where={"dataSourceId": data_source_id}):
        fqn = table.fullyQualifiedName
        table_name = unqualified_table_name(fqn)
        lower_table_name = table_name.lower()

        schema[lower_table_name] = {"name": table_name, "columns": {}}

        for column in db.datasourcetablecolumn.find_many(where={"dataSourceTableDescriptionId": table.id}):
            schema[lower_table_name]["columns"][column.name.lower()] = {"name": column.name}

    return schema
