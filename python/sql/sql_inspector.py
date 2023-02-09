"""
The SqlInspector parses a SQL query and provides the following insights:
1. What tables, columns, and string values (in where or having clauses) does
   the sql query touch
2. Any tables or columns that are accessed but not in the schema.

It also provides a graph representation of how tables and columns pass through
each node in the AST. Databases, tables, and columns are resolved with a
somewhat complex lookup algoirthm that requires resolving as the query AST
is constructed (in a specific order), or resolving by searching only the
nodes above and to the left of the current node. (similar result). I opted
to resolve as the AST is constructed because it is more efficient.

Each node in the AST has columns and tables that are passed through. The code
below uses the visitor pattern and each class is responsible for determining
which columns and tables are passed through. SELECT nodes filter what
columns are passed through in their expressions. Subqueries in the FROM
section of a SELECT return all columns in the subqueries SELECT expressions,
and can be aliased to look like a table. As you go up the tree, columns
replace merge based on left to right order, and you can alias an existing
alias.

Columns can be looked up by either the alias, or the original column
name. Tables, if aliased, can only be looked up by the alias.


SELECT statements have a specific order their arguments need to be parsed in.
Tables and columns (and any associated aliases) need to look up based on their
parent SELECT, not what is under them in the tree, at the point in time when
they are run.

Select's need to have children run in the following order:
1. FROM
2. JOIN's
3. SELECT expressions
4. WHERE
5. GROUP BY
6. HAVING
7. ORDER BY
8. LIMIT
"""

# TODO: Don't forget: EXISTS, UNION, UNION ALL, EXCEPT

import os
from dataclasses import dataclass

from sqlglot import parse_one

from python.sql.nodes.base import Base
from python.sql.nodes.builder import add_child
from python.sql.types import SimpleSchema, SqlState
from python.utils.logging import log


@dataclass(init=False)
class SqlInspector:
    """
    The SqlInspector takes in a string of SQL and builds up an AST loosly
    based on sqlglot's AST, but changed for better introspection and tracing
    of data flow.
    """

    start_state: SqlState  # = field(init=False, repr=False)
    root: Base

    def __init__(self, sql: str, schema: SimpleSchema, dialect: str = "snowflake"):
        ast = parse_one(sql, dialect)

        if os.getenv("DEBUG"):
            log.debug("AST: ")
            log.debug(ast)

        self.start_state = {
            "node": ast,
            "select": None,
            "schema": schema,
            "branch": "select",
            "node": ast,
            "touches": {},
        }

        # Start building the tree, first node atm should be a SELECT
        self.root = add_child(self.start_state, [], ast)

    def touches(self):
        return self.root.state["touches"]
