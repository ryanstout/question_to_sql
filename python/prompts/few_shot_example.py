"""
Takes in the SQL for a few shot example and generates the schema ranking of the tables and columns used in this example.

We can merge the schema ranking to make sure the tables/columns are included in the prompt schema. If those aren't
in there, gpt does not do well.
"""

from python.schema.ranker import ElementRank
from python.sql.sql_inspector import SqlInspector
from python.sql.sql_parser import SqlParser
from python.sql.types import SimpleSchema
from python.sql.utils.touch_points import convert_db_element_to_db_element_ids


class FewShotExample:
    schema_rankings: list[ElementRank]

    def __init__(self, data_source_id: int, simple_schema: SimpleSchema, sql: str):
        """
        Use SqlInspector to compute the element rankings for the example
        """

        sql_inspector = SqlInspector(sql, simple_schema, SqlParser.in_dialect)

        db_elements = sql_inspector.touches().keys()

        self.schema_rankings = []

        for db_element in db_elements:
            db_element_ids = convert_db_element_to_db_element_ids(data_source_id, db_element)
            self.schema_rankings.append(
                ElementRank(
                    table_id=db_element_ids.table,
                    column_id=db_element_ids.column,
                    value_hint=db_element_ids.value,
                    score=100.0,
                )
            )
