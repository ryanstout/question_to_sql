import os
from dataclasses import dataclass, field

from python.sql.exceptions import ColumnNotFoundError
from python.sql.nodes.base import Base
from python.sql.types import ChildrenType, ColumnsType, SqlState


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
                raise Exception("Parent select not assigned")

        return self._columns
