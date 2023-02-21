from dataclasses import dataclass

from python.sql.nodes.base import Base
from python.sql.types import DbElement, SqlState


@dataclass(init=False)
class EQ(Base):
    value_str: str

    def __init__(self, state: SqlState, value_str: str):
        super().__init__(state)
        self.value_str = value_str

    def resolve(self):
        child_columns = super().columns()

        for ((_table, _col), col_refs) in child_columns.items():
            for col_ref in col_refs:
                # When we have an EQ node that matches a string, we want to track
                # the column(s) and value that it matches against.
                self._track_touch(DbElement(col_ref.table.name, col_ref.name, self.value_str))
