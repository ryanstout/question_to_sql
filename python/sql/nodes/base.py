from dataclasses import dataclass, field
from typing import List, Tuple

from deepmerge import always_merger as deep

from python.sql.types import ChildrenType, ColumnsType, SqlState, TablesType


@dataclass(init=False)
class Base:
    """
    Matches a similar structure to sqlglot AST args, but using Node instead
    """

    state: SqlState = field(init=False, repr=False)
    children: ChildrenType

    def __init__(self, state: SqlState):
        """
        Tracks the relevant state for the current node
        """
        self.state = state
        self.children = {}

    def resolve(self):
        """
        Stub method, called before this node is added to the tree, but after
        children are added.
        """
        pass

    def tables(self) -> TablesType:
        """
        Return concat of the child tables
        """
        tables: TablesType = {}
        for child in self.all_children():
            # Merge key,values overriding the pervious
            tables = deep.merge(tables, child.tables())

        return tables

    def columns(self) -> ColumnsType:
        """
        Most nodes overwrite columns by name/alias instead of merging like
        would happen in a CONCAT node or something.
        """
        # Return a dict going from alias (or full name) to a list of columns
        return merge_columns(self.all_children())

    def all_children(self) -> List["Base"]:
        """
        Returns a list of all children, in the order of the Dict first, then
        any lists
        """
        all_children = []
        for child in self.children.values():
            for c in child:
                all_children.append(c)

        return all_children

    def mark_touched(self):
        """Marks all tables and columns in this node as touched"""
        touches = self.state["touches"]
        for table_refs in self.tables().values():
            for table_ref in table_refs:
                self._track_touch((table_ref.name, None, None))

        for columns in self.columns().values():
            for column in columns:
                self._track_touch((column.table.name, column.name, None))

    def _track_touch(self, key: Tuple[str, str | None, str | None]):
        """Tracks a touch on a column"""
        touches = self.state["touches"]
        if key not in touches:
            touches[key] = 0
        touches[key] += 1

    # def __repr__(self, indent: int = 0):
    #     indent_spaces = " " * indent

    #     output = ""
    #     output += f"{indent_spaces}<{self.__class__.__name__}\n"
    #     for key, child in self.children.items():
    #         if isinstance(child, List):
    #             output += f"{indent_spaces}  {key}:\n"
    #             for c in child:
    #                 output += f"{indent_spaces}    {c.__repr__(indent+4)}\n"
    #         else:
    #             output += f"{indent_spaces}  {key}: {child.__repr__(indent+2)}\n"
    #     output += f"{indent_spaces}>\n"


def merge_columns(nodes: List[Base]) -> ColumnsType:
    """
    Merges the columns from a list of nodes into a single ColumnsType dict
    """
    columns: ColumnsType = {}
    for node in nodes:
        columns.update(node.columns())

    return columns
