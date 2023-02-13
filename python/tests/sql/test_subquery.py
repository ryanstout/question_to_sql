from pprint import pprint

import pytest
from rich import print

from python.sql.exceptions import ColumnNotFoundException, TableNotFoundException
from python.sql.sql_inspector import SqlInspector


def test_subquery1():
    inspector = SqlInspector(
        """
        SELECT col1, c3 FROM (SELECT col1, col3 as c3 FROM table2);
        """,
        {"table1": ["col1", "col2"], "table2": ["col1", "col3"]},
    )
    assert inspector.touches() == {("table2", None, None): 1, ("table2", "col1", None): 2, ("table2", "col3", None): 3}


def test_subquery_with_subquery_aliased():
    inspector = SqlInspector(
        """
        SELECT col1, t1.c3 FROM (SELECT col1, col3 as c3 FROM table2) as t1;
        """,
        {"table1": ["col1", "col2"], "table2": ["col1", "col3"]},
    )
    assert inspector.touches() == {("table2", None, None): 1, ("table2", "col1", None): 2, ("table2", "col3", None): 3}


def test_subquery_pass_through():
    inspector = SqlInspector(
        """
        SELECT col1, t1.col1 FROM (SELECT col1 FROM table2) as t1;
        """,
        {"table1": ["col1", "col2"], "table2": ["col1", "col3"]},
    )
    assert inspector.touches() == {("table2", None, None): 1, ("table2", "col1", None): 3}

    with pytest.raises(ColumnNotFoundException):
        inspector = SqlInspector(
            """
            SELECT col1, table2.col3 FROM (SELECT col1 FROM table2);
            """,
            {"table1": ["col1", "col2"], "table2": ["col1", "col3"]},
        )

    with pytest.raises(ColumnNotFoundException):
        inspector = SqlInspector(
            """
            SELECT col1, t1.col3 FROM (SELECT col1 FROM table2) as t1;
            """,
            {"table1": ["col1", "col2"], "table2": ["col1", "col3"]},
        )