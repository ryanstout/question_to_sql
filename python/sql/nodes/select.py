from dataclasses import dataclass

from python.sql.nodes.base import Base, merge_columns


@dataclass(init=False)
class Select(Base):
    def filtered_columns(self):
        """
        When getting columns for the select itself, we filter by the
        expressions.
        """

        expression_nodes = self.children["expressions"]
        return merge_columns(expression_nodes)

    def inner_columns(self):
        """
        When getting columns for the elements inside of the SELECT, we combine
        all of the sub-node columns.
        """
        return super().columns()
