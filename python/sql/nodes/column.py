import os
from dataclasses import dataclass, field

from python.sql.exceptions import ColumnNotFoundError
from python.sql.nodes.base import Base
from python.sql.types import ChildrenType, ColumnsType, SqlState
from python.sql.utils.snowflake_keywords import SNOWFLAKE_KEYWORDS


@dataclass(init=False)
class Column(Base):
    name: str
    children: ChildrenType = field(repr=False)
    _columns: ColumnsType | None

    def __init__(self, state: SqlState, name: str, table_alias: str | None):
        super().__init__(state)
        self.children = {}
        self.name = name
        self.table_alias = table_alias
        self._columns = None

        # When we add a child, we look up the column on the SELECT statement
        # (assuming the column has been added from a FROM statement, JOIN, or
        # previous column alias)
        self.mark_touched()

    def columns(self) -> ColumnsType:
        if not self._columns:
            parent_select = self.state["select"]
            if parent_select:

                columns = parent_select.inner_columns()

                key = (self.table_alias, self.name)
                column = columns.get(key)

                # See if the column exists on the SELECT at this point, only return
                # the matched column
                if column is not None:
                    # Rename the column to the correct casing from the schema
                    self.correct_case(column)

                    # Cache the column once it's resolved to prevent stack
                    # explosion
                    self._columns = {key: column}
                    return {key: column}
                else:
                    if os.environ.get("SQL_PARSING_DEBUG"):
                        print("COLUMNS: ")
                        for key, column in columns.items():
                            print(key, column)
                    raise ColumnNotFoundError(f"Unable to resolve column ({self.table_alias}.{self.name})")
            else:
                raise ValueError("Parent select not assigned")

        return self._columns

    def correct_case(self, column):
        """
        When a table, column, or alias is a keyword, we need to quote it, and then it becomes case sensitive.

        Below does not do the quoting, but it updates to the correct case based on the actual database schema.
        """
        if (
            self.name.upper() not in SNOWFLAKE_KEYWORDS
            and self.table_alias
            and self.table_alias.upper() not in SNOWFLAKE_KEYWORDS
        ):
            return

        for column_ref in column:
            simple_table = self.state["schema"].get(column_ref.table.name)
            if simple_table:
                simple_column = simple_table["columns"].get(self.name.lower())
                if simple_column:
                    if self.name.upper() in SNOWFLAKE_KEYWORDS:
                        self.state["node"].args["this"].args["this"] = simple_column["name"]

                    if self.table_alias is not None and self.table_alias.upper() in SNOWFLAKE_KEYWORDS:
                        self.state["node"].args["table"].args["this"] = simple_table["name"]
                    break
