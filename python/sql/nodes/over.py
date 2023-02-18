from dataclasses import dataclass

from python.sql.nodes.base import Base, merge_columns


@dataclass(init=False)
class Over(Base):
    def columns(self):
        """
        The output from over ends up coming from the left side
        """

        return merge_columns(self.children["this"])
