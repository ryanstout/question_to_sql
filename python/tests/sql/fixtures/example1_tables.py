# A simple schema to work with, with a few tables
import json

from python.sql.types import SimpleSchema
from python.utils.db import application_database_connection

from prisma import Json
from prisma.enums import DataSourceType

db = application_database_connection()

example1_tables: SimpleSchema = {
    "table1": {
        "name": "DB.TABLE1",
        "columns": {
            "column1": {
                "name": "COLUMN1",
            },
            "column2": {
                "name": "COLUMN2",
            },
        },
    },
    "table2": {
        "name": "DB.TABLE2",
        "columns": {
            "column3": {
                "name": "COLUMN3",
            },
            "column4": {
                "name": "COLUMN4",
            },
        },
    },
}


def example1_setup():
    # Create stub datasource
    data_source = db.datasource.create(
        data={"id": 1, "name": "example1", "credentials": Json({}), "type": DataSourceType.SNOWFLAKE}
    )

    if not data_source:
        raise ValueError("Failed to create data source")

    for _, table_val in example1_tables.items():
        table_obj = db.datasourcetabledescription.create(
            data={"dataSourceId": data_source.id, "fullyQualifiedName": table_val["name"]}
        )

        print(table_obj)

        if table_obj:
            # Create the columns
            for _, column_val in table_val["columns"].items():
                properties = Json({})

                db.datasourcetablecolumn.create(
                    data={
                        "dataSourceId": data_source.id,
                        "dataSourceTableDescriptionId": table_obj.id,
                        "name": column_val["name"],
                        "type": "VARCHAR",
                        "kind": "COLUMN",
                        "isNull": False,
                        "distinctRows": 5,
                        "rows": 1000,
                        "extendedProperties": properties,
                    }
                )
        else:
            raise ValueError(f"Table failed to create: {table_val['name']}, {table_obj!r}")
