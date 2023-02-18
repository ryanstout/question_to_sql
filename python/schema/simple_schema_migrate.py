"""
Migrate helper for moving tests from old format
"""

from python.sql.types import SimpleSchema


def migrate(old_simple_schema):
    new_schema: SimpleSchema = {}
    for table_name, columns in old_simple_schema.items():
        new_schema[table_name] = {"name": table_name, "columns": {}}
        for column_name in columns:
            new_schema[table_name]["columns"][column_name.lower()] = {"name": column_name}

    print(new_schema)

    return None
