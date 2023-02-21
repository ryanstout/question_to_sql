# To full resolve columns, we need a simple representation of the schema
#
# {
#  "table_name1": ["col1", "col2"],
#  "table_name2"...
# }
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, NamedTuple, Tuple, TypeAlias, TypedDict

if TYPE_CHECKING:
    from python.sql.nodes.base import Base
    from python.sql.nodes.select import Select

from sqlglot import exp

from python.sql.refs import (  # pylint: disable=unused-import,ungrouped-imports
    ColumnRef,
    TableRef,
)

# SimpleSchema provides a way for the SqlInspector to look up the table and column names. Because we usually need to
# do case insensitive lookups, we store the names in lowercase, then have a mapping back to the original.

# simple_schema = {
#   "table1": {name: "Table1", "columns": {"column1": "Column1", "column2": "Column2"}},
#   "table2": {name: "Table2", "columns": {"column1": "Column1", "column2": "Column2"}},
#   ...
# }


class SimpleColumn(TypedDict):
    name: str  # the original name of the column, not lowercased


class SimpleTable(TypedDict):
    name: str  # the original name of the table, not lowercased
    columns: Dict[str, SimpleColumn]  # the original name of the column, not lowercased


SimpleSchema: TypeAlias = Dict[str, SimpleTable]

TablesType: TypeAlias = Dict[str, List["TableRef"]]

# Example: {
# ("table1", "column1"): [ColumnRef()],
# (None, "column1"): [ColumnRef()],
# ("table1", "column2"): [ColumnRef()],
# ...
# }
ColumnsType: TypeAlias = Dict[Tuple[str | None, str], List["ColumnRef"]]
ChildrenType: TypeAlias = Dict[str, List["Base"]]

# A DbElement points to either a table, column, or value. If pointing to a value for example, the table and column
# will also be specified.
class DbElement(NamedTuple):
    table: str
    column: str | None
    value: str | None


# When querying the faiss index, we don't need most of the results, so just working with the id's for table and column
# means we can avoid lookups when we don't end up using the DbElementIds
class DbElementIds(NamedTuple):
    table: int
    column: int | None
    value: str | None


# value `int` represents the how many times the entry was touched/used
DbTouchPointCounts: TypeAlias = Dict[DbElement, int]


# Each individual DbElement can be given a score from the various faiss indicies
@dataclass
class ElementScores:
    # Scores for each of the indexes
    table_names_score: float | None = field(default=None)
    column_names_score: float | None = field(default=None)
    table_and_column_names_score: float | None = field(default=None)
    column_name_and_all_column_values_score: float | None = field(default=None)
    table_column_and_value_score: float | None = field(default=None)
    values_score: float | None = field(default=None)


class SqlState(TypedDict):
    """
    Represents the state for each node, we create a shallow copy at each step,
    then modify it a little as we pass it down
    """

    schema: SimpleSchema
    select: "Select | None"  # The Select node will update to self for root
    branch: str
    node: exp.Expression
    dialect: str  # 'postgres' | 'snowflake'

    # What tables, columns, and values (as a string) does the sql query touch
    # and therefore need to be in the in the prompt schema
    touches: DbTouchPointCounts
