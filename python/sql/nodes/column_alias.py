from dataclasses import dataclass
from pprint import pprint

from python.sql.nodes.base import Base
from python.sql.nodes.count_star import CountStar
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

            if len(child_columns) == 0:
                # this can happen if the alias is for a literal string expression
                return {}

            if len(child_columns) > 1:
                raise ValueError(
                    f"ColumnAlias should only have one column in children:\n{self.state['node']!r}\n\n{self}"
                )
            child_column = next(iter(child_columns.values()))

            key = (self.table_qualifier, self.alias)
            self._columns = {}

            self._columns.update({key: child_column})
            self._columns.update({(None, self.alias): child_column})

        return self._columns
