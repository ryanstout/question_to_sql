from python.sql.nodes.base import Base
from python.sql.nodes.select import Select
from python.sql.types import ColumnsType, SqlState, TablesType


class Subquery(Base):
    """
    Pass through unqualified columns, but not qualified columns.
    (You can't use table.column to access a column in a FROM clause outside of
    the subquery)
    If there's an alias, then we add alias.column versions of the column

    Subqueries propigate up only the unqualified column names

    """

    alias: str | None

    def __init__(
        self,
        state: SqlState,
        alias: str | None,
    ):
        super().__init__(state)
        self.alias = alias

    def tables(self) -> TablesType:
        """
        A subquery only looks like a table if you add an alias
        """

        child_tables = super().tables()

        if self.alias:
            merge_table_refs = []
            for table_refs in child_tables.values():
                merge_table_refs.extend(table_refs)
            return {self.alias: merge_table_refs}
        else:
            return {}

    def columns(self) -> ColumnsType:
        """
        Reject qualified columns, add aliased columns if an alias is set
        """
        child_select = self.children["select"][0]

        if not isinstance(child_select, Select):
            raise Exception(f"Subquery select not instance of Select(): {child_select = }")

        child_select_cols = child_select.filtered_columns()

        # Filter out qualified columns
        columns: ColumnsType = {k: v for (k, v) in child_select_cols.items() if k[0] is None}

        # Add aliased versions of the columns
        if self.alias:
            aliased_columns: ColumnsType = {(self.alias, k[1]): v for (k, v) in child_select_cols.items()}
            columns.update(aliased_columns)

        return columns
