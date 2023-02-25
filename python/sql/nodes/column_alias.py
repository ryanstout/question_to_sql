from dataclasses import dataclass

from python.sql.nodes.base import Base
from python.sql.refs import ColumnRef
from python.sql.types import ColumnsType, SqlState


@dataclass(init=False)
class ColumnAlias(Base):
    alias: str
    table_qualifier: str | None
    _columns: ColumnsType | None

    def __init__(
        self,
        state: SqlState,
        alias: str,
        table_qualifier: str | None,
    ):
        super().__init__(state)
        self._columns = None

        self.alias = alias
        self.table_qualifier = table_qualifier

    def resolve(self):
        self.mark_touched()

    def columns(self) -> ColumnsType:
        """
        Look at this nodes children only to build up the columns, the
        column references themselves will look at what has been registered
        on the SELECT statement.

        Think of this as a rebinding to an already resolved column
        """

        if not self._columns:
            child_columns = super().columns()

            self._columns = {}

            # Get all child column refs into a single list
            child_col_refs: list[ColumnRef] = []

            for child_column in child_columns.values():
                child_col_refs += child_column

            key = (self.table_qualifier, self.alias)

            self._columns.update({key: child_col_refs})
            self._columns.update({(None, self.alias): child_col_refs})

        return self._columns
