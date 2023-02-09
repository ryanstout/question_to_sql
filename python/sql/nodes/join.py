from dataclasses import dataclass

from python.sql.nodes.base import Base


@dataclass(init=False)
class Join(Base):
    pass
