"""
Creates a short representation of a schema to be fed to chatgpt
"""

from python.utils import sql
from python.utils.db import application_database_connection

db = application_database_connection()


def create_short_format(data_source_id: int):
    tables = db.datasourcetabledescription.find_many(where={"dataSourceId": data_source_id}, include={"columns": True})

    output = ""

    for table in tables:
        unqualified_name = sql.unqualified_table_name(table.fullyQualifiedName)
        output += f"table: {unqualified_name.lower()}\n"

        assert table.columns is not None

        for column in table.columns:
            output += f" {column.name.lower().replace('_', ' ')}\n"

        output += "\n"

    return output


if __name__ == "__main__":
    print(create_short_format(1))
