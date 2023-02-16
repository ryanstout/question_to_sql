from dataclasses import dataclass, field

from python.sql.exceptions import TableNotFoundError
from python.sql.nodes.base import Base
from python.sql.refs import ColumnRef, TableRef
from python.sql.types import ChildrenType, ColumnsType, SqlState, TablesType


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
        self._track_touch((self.name, None, None))

    def tables(self) -> TablesType:
        if len(self._tables) == 0:
            table_ref = TableRef(self.name)
            if self.name in self.state["schema"]:
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
        table_columns = self.state["schema"][self.name]

        if not table_columns:
            raise TableNotFoundError(f"Table {self.name} not found in schema")

        if not self._columns:
            self._columns = {}
            for column_name in table_columns:
                column_ref = ColumnRef(column_name, table[0])

                # Add unqualified
                self._columns[(None, column_name)] = [column_ref]

                if self.alias:
                    # Add qualified table
                    self._columns[(self.alias, column_name)] = [column_ref]
                else:
                    # Add fully qualified
                    self._columns[(table[0].name, column_name)] = [column_ref]

        return self._columns
