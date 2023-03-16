from dataclasses import dataclass, field

from python.sql.exceptions import TableNotFoundError
from python.sql.nodes.base import Base
from python.sql.refs import ColumnRef, TableRef
from python.sql.types import ChildrenType, ColumnsType, DbElement, SqlState, TablesType
from python.sql.utils.snowflake_keywords import SNOWFLAKE_KEYWORDS


@dataclass(init=False)
class Table(Base):
    """
    When a table is given an alias, this effectively renames the table for
    all accesses. (Unlike columns where it is just an alias)
    """

    name: str
    children: ChildrenType = field(repr=False)
    _tables: TablesType
    _columns: ColumnsType | None = field(repr=False)

    def __init__(self, state: SqlState, name: str, alias: str | None):
        super().__init__(state)
        self.name = name
        self.alias = alias
        self._tables = {}
        self._columns = None

        # Mark the table only as touched
        self._track_touch(DbElement(self.name, None, None))

    def tables(self) -> TablesType:
        if len(self._tables) == 0:
            table_ref = TableRef(self.name)
            simple_table = self.state["schema"].get(self.name.lower())

            if simple_table:
                if self.name.upper() in SNOWFLAKE_KEYWORDS:
                    # Update the identifier to the table name with the correct casing (if the name is a keyword, we have
                    # to quote it and then it will be looked up in a case sensisitive way)
                    node = self.state["node"]
                    node.args["this"].args["this"] = simple_table["name"]

                if self.alias:
                    self._tables = {self.alias: [table_ref]}
                else:
                    self._tables = {self.name: [table_ref]}
            else:
                raise TableNotFoundError(f"Table {self.name} not found in schema")

        return self._tables

    def columns(self) -> ColumnsType:
        table = self.tables().get(self.alias or self.name)
        if not table:
            raise TableNotFoundError(f"Table {self.name} not found")
        # Grab the columns from the schema for the table
        simple_table = self.state["schema"].get(self.name.lower())

        if not simple_table:
            raise TableNotFoundError(f"Table {self.name} not found in schema")

        if not self._columns:
            self._columns = {}
            for column_name_lower, _ in simple_table["columns"].items():
                column_ref = ColumnRef(column_name_lower, table[0])

                # Add unqualified
                self._columns[(None, column_name_lower)] = [column_ref]

                if self.alias:
                    # Add qualified table
                    self._columns[(self.alias, column_name_lower)] = [column_ref]
                else:
                    # Add fully qualified
                    self._columns[(table[0].name, column_name_lower)] = [column_ref]

        return self._columns

    def resolve(self):
        # We need to resolve table so the capitalization correction will run even if .tables is never called
        self.columns()
