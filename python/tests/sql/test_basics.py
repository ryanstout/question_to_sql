from pprint import pprint

import pytest
from rich import print

from python.sql.exceptions import ColumnNotFoundException, TableNotFoundException
from python.sql.sql_inspector import SqlInspector


def test_simple_multitable_select():
    inspector = SqlInspector(
        """
        SELECT col1, col2 as c FROM table1, table2;
        """,
        {"table1": ["col1", "col3"], "table2": ["col2"]},
    )
    assert inspector.touches() == {
        ("table1", None, None): 1,
        ("table2", None, None): 1,
        ("table1", "col1", None): 1,
        ("table2", "col2", None): 2,
    }


def test_lookup_table_by_unaliased_when_alias_supplied():
    inspector = SqlInspector(
        """
        SELECT col1, col2 FROM table1 as t1, table2 as t2;
        """,
        {"table1": ["col1"], "table2": ["col2"]},
    )
    assert inspector.touches() == {
        ("table1", None, None): 1,
        ("table2", None, None): 1,
        ("table1", "col1", None): 1,
        ("table2", "col2", None): 1,
    }


def test_simple_multitable_select_with_alias_where_aliases_used():
    inspector = SqlInspector(
        """
        SELECT t2.col1, t1.col2 FROM table1 as t1, table2 as t2;
        """,
        {"table1": ["col1", "col2"], "table2": ["col1", "col2"]},
    )
    assert inspector.touches() == {
        ("table1", None, None): 1,
        ("table2", None, None): 1,
        ("table2", "col1", None): 1,
        ("table1", "col2", None): 1,
    }


def test_table_alias_should_not_allow_access_via_original_name():
    with pytest.raises(ColumnNotFoundException):
        inspector = SqlInspector(
            """
            SELECT table1.col1 FROM table1 as t1;
            """,
            {"table1": ["col1", "col2"]},
        )


def test_simple_with_column_alias():
    inspector = SqlInspector(
        """
        SELECT t1.col1 as alias1, t2.col2 as alias2 FROM table1 as t1, table2 as t2;
        """,
        {"table1": ["col1", "col2"], "table2": ["col2"]},
    )
    assert inspector.touches() == {
        ("table1", None, None): 1,
        ("table2", None, None): 1,
        ("table1", "col1", None): 2,
        ("table2", "col2", None): 2,
    }


def test_alias_on_alias():
    inspector = SqlInspector(
        """
        SELECT col1 as col1_alias, col1_alias as col1_alias_alias FROM table1, table2;
        """,
        {"table1": ["col1", "col2"], "table2": ["col2"]},
    )
    assert inspector.touches() == {("table1", None, None): 1, ("table2", None, None): 1, ("table1", "col1", None): 4}


def test_unqualified_select_star():
    inspector = SqlInspector(
        """
        SELECT * FROM table1, table2;
        """,
        {"table1": ["col1", "col2"], "table2": ["col2", "col3"]},
    )
    assert inspector.touches() == {
        ("table1", None, None): 1,
        ("table2", None, None): 1,
        ("table1", "col1", None): 1,
        ("table2", "col2", None): 1,
        ("table2", "col3", None): 1,
    }


def test_qualified_select_star():
    inspector = SqlInspector(
        """
        SELECT table1.* FROM table1, table2;
        """,
        {"table1": ["col1", "col2"], "table2": ["col2", "col3"]},
    )
    assert inspector.touches() == {
        ("table1", None, None): 1,
        ("table2", None, None): 1,
        ("table1", "col1", None): 1,
        ("table1", "col2", None): 1,
    }
