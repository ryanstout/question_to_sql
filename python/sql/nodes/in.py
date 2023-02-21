from dataclasses import dataclass

from python.sql.nodes.base import Base
from python.sql.types import SqlState


@dataclass(init=False)
class In(Base):
    def __init__(self, state: SqlState):
        """
        If the IN has strings on the right hand side, we add these as value matches
        """
        super().__init__(state)
