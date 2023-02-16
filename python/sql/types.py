# To full resolve columns, we need a simple representation of the schema
#
# {
#  "table_name1": ["col1", "col2"],
#  "table_name2"...
# }
from typing import TYPE_CHECKING, Dict, List, Tuple, TypeAlias, TypedDict

if TYPE_CHECKING:
    from python.sql.nodes.base import Base
    from python.sql.nodes.select import Select

from sqlglot import exp

from python.sql.refs import ColumnRef, TableRef

SimpleSchema: TypeAlias = Dict[str, List[str]]

TablesType: TypeAlias = Dict[str, List["TableRef"]]

# Example: {
# ("table1", "column1"): [ColumnRef()],
# (None, "column1"): [ColumnRef()],
# ("table1", "column2"): [ColumnRef()],
# ...
# }
ColumnsType: TypeAlias = Dict[Tuple[str | None, str], List["ColumnRef"]]
ChildrenType: TypeAlias = Dict[str, List["Base"]]


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
    touches: Dict[Tuple[str, str | None, str | None], int]
