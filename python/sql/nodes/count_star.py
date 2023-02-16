from dataclasses import dataclass

from sqlglot import exp

from python.sql.nodes.base import Base
from python.sql.types import ColumnsType, SqlState


@dataclass(init=False)
class CountStar(Base):
    def __init__(self, state: SqlState):
        super().__init__(state)

    def columns(self) -> ColumnsType:
        """
        Creates a table=None, column=None alias for the count(*) expression so it can be aliased up the tree
        """

        return {(None, "{count}"): []}
