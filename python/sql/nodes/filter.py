from dataclasses import dataclass

from python.sql.exceptions import FilterNotSupportedError
from python.sql.nodes.base import Base
from python.sql.types import SqlState


@dataclass(init=False)
class Filter(Base):
    def __init__(self, state: SqlState):
        """
        Filter is not supported in snowflake, so we raise an exception when constructing if the dialect is snowflake
        """
        if state["dialect"] == "snowflake":
            raise FilterNotSupportedError()
        else:
            super().__init__(state)
