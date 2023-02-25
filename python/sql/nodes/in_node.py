"""
When an IN expression has string values, we use those as value matches.

NOTE: Python doesn't like having a class named "In", so we call it "InNode"
"""

from dataclasses import dataclass
from typing import List

from sqlglot import exp

from python.sql.nodes.base import Base
from python.sql.types import DbElement, SqlState


@dataclass(init=False)
class InNode(Base):
    def __init__(self, state: SqlState, in_nodes: List[exp.Expression]):
        super().__init__(state)
        self.in_nodes = in_nodes

    def resolve(self):
        # TODO: This should also support expressions in the IN clause (a scalar subquery for example)

        # For some reason string values in an IN expression come in as exp.Columns
        if len(self.in_nodes) > 0 and isinstance(self.in_nodes[0], exp.Column):
            child_columns = super().columns()

            for in_node in self.in_nodes:
                for ((_table, _col), col_refs) in child_columns.items():
                    for col_ref in col_refs:
                        # When we have an IN node that's possible values are strings, we want to track
                        # the column(s) and value that it matches against.
                        self._track_touch(
                            DbElement(col_ref.table.name, col_ref.name, in_node.args["this"].args["this"])
                        )
