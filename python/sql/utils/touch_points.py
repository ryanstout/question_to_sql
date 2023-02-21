from python.schema.simple_schema_builder import SimpleSchemaBuilder
from python.sql.sql_inspector import SqlInspector
from python.sql.sql_parser import SqlParser
from python.sql.types import DbElement, DbElementIds
from python.utils.db import application_database_connection
from python.utils.sql import unqualified_table_name

db = application_database_connection()


def get_touch_points_ids(sql: str, data_source_id: int) -> list[DbElementIds]:
    """
    Touch points indicates all tables, columns, and column values that are referenced
    in the incoming SQL.

    Ex: ('order', 'financial_status', 'paid')
    """
    simple_schema = SimpleSchemaBuilder().build(db, data_source_id)
    ast = SqlParser().run(sql)
    inspector = SqlInspector(ast, simple_schema, SqlParser.in_dialect)

    # Loop through the touch points and convert them from DbElements to DbElementIds
    touch_point_ids: list[DbElementIds] = []
    for touch_point in inspector.touches().keys():
        touch_point_ids.append(convert_db_element_to_db_element_ids(data_source_id, touch_point))

    return touch_point_ids


def convert_db_element_to_db_element_ids(data_source_id: int, element: DbElement) -> DbElementIds:
    """
    Use the database to lookup the id's from table and column from a DbElementId
    """

    table_name, column_name, value_str = element

    if not table_name:
        raise ValueError("Table name is required")

    # TODO: endswith is probably going to slow things down
    table = db.datasourcetabledescription.find_first(
        where={"dataSourceId": data_source_id, "fullyQualifiedName": {"endswith": "." + table_name.upper()}}
    )
    if not table:
        raise ValueError(f"Table with name {table_name} not found")

    table_id = table.id

    if column_name:
        # TODO: The .upper() is a place holder, switch to case insensitive search or some cached lookup
        column = db.datasourcetablecolumn.find_first(
            where={"dataSourceTableDescriptionId": table.id, "name": column_name.upper()}
        )
        if not column:
            raise ValueError(f"Column with name {column_name} not found on table {table_name}")
        column_id = column.id
    else:
        column_id = None

    return DbElementIds(table_id, column_id, value_str)


def convert_db_element_ids_to_db_element(element: DbElementIds) -> DbElement:
    """
    Convert a DbElementIds to a DbElement by looking up table/column names in the database
    """

    table_id, column_id, value_str = element

    if not table_id:
        raise ValueError("Table id is required")

    table = db.datasourcetabledescription.find_first(where={"id": table_id})
    if not table:
        raise ValueError(f"Table with id {table_id} not found")

    table_name = unqualified_table_name(table.fullyQualifiedName)

    if column_id:
        column = db.datasourcetablecolumn.find_first(where={"id": column_id})
        if not column:
            raise ValueError(f"Column with id {column_id} not found")
        column_name = column.name
    else:
        column_name = None

    return DbElement(table_name, column_name, value_str)
