from dataclasses import dataclass

from sqlglot import exp

from python.sql.nodes.base import Base
from python.sql.types import ColumnsType, SqlState


@dataclass(init=False)
class Star(Base):
    _columns: ColumnsType

    def __init__(self, state: SqlState, table_alias: str | None):
        super().__init__(state)
        self.table_alias = table_alias

    def resolve(self):
        parent_select = self.state["select"]
        if parent_select:
            self._columns = parent_select.inner_columns().copy()

            # Reject any that don't of table qualifier or None
            self._columns = {k: v for k, v in self._columns.items() if k[0] == self.table_alias}

            # All columns pulled by the star get touched
            self.mark_touched()
        else:
            raise Exception("Parent select not provided")

    def columns(self):
        """
        Star touches and returns all columns accessable on the current select
        """

        return self._columns or {}
