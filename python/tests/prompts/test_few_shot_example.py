from python.prompts.few_shot import revert_sql_for_few_shot
from python.prompts.few_shot_example import FewShotExample
from python.schema.simple_schema_builder import build_simple_schema
from python.sql.types import DbElement, DbElementIds
from python.sql.utils.touch_points import convert_db_element_ids_to_db_element
from python.tests.sql.fixtures.example1_tables import example1_setup
from python.tests.test_utils.database import teardown


def test_few_shot_example():
    teardown()
    example1_setup()

    # schema = example1_tables
    schema = build_simple_schema(1)
    example = FewShotExample(
        1, schema, "SELECT column1, column3 FROM table1, table2 WHERE table1.column2=table2.column4;"
    )

    # Map rankings back to DbElements
    rankings = [
        convert_db_element_ids_to_db_element(DbElementIds(ei.table_id, ei.column_id, ei.value_hint))
        for ei in example.schema_rankings
    ]

    assert rankings == [
        DbElement(table="TABLE1", column=None, value=None),
        DbElement(table="TABLE2", column=None, value=None),
        DbElement(table="TABLE1", column="COLUMN1", value=None),
        DbElement(table="TABLE2", column="COLUMN3", value=None),
        DbElement(table="TABLE1", column="COLUMN2", value=None),
        DbElement(table="TABLE2", column="COLUMN4", value=None),
    ]


def test_revert_sql_for_few_shot():
    sql = """SELECT FIRST_NAME FROM "ORDER" WHERE ID=5;"""
    reverted_sql = revert_sql_for_few_shot(sql)
    assert (
        reverted_sql
        == """SELECT
  first_name
FROM "order"
WHERE
  id = 5;"""
    )
