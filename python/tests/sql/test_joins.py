from pprint import pprint

import pytest
from rich import print

from python.sql.exceptions import ColumnNotFoundError, TableNotFoundError
from python.sql.sql_inspector import SqlInspector


def test_inner_join():
    inspector = SqlInspector(
        """
        SELECT t1.col1, t2.col2 FROM table1 as t1 INNER JOIN table2 as t2 ON t1.col1 = t2.col2;
        """,
        {"table1": ["col1", "col4"], "table2": ["col2", "col3"]},
    )
    assert inspector.touches() == {
        ("table1", None, None): 1,
        ("table2", None, None): 1,
        ("table1", "col1", None): 2,
        ("table2", "col2", None): 2,
    }


def test_inner_join2():
    inspector = SqlInspector(
        # How many average orders are there for orders over $500?
        """
        SELECT SUM(quantity) FROM orders INNER JOIN line_items ON id=order_id WHERE total_dollars > 500;
        """,
        {"orders": ["id", "total_dollars"], "line_items": ["order_id", "quantity"]},
    )
    assert inspector.touches() == {
        ("orders", None, None): 1,
        ("line_items", None, None): 1,
        ("orders", "id", None): 1,
        ("line_items", "order_id", None): 1,
        ("line_items", "quantity", None): 1,
        ("orders", "total_dollars", None): 1,
    }


def test_inner_join_with_aliases():
    inspector = SqlInspector(
        # How many average orders are there for orders over $500?
        """
        SELECT SUM(quantity) FROM orders as o INNER JOIN line_items as li ON o.id=li.order_id WHERE o.total_dollars > 500;
        """,
        {"orders": ["id", "total_dollars"], "line_items": ["order_id", "quantity"]},
    )
    assert inspector.touches() == {
        ("orders", None, None): 1,
        ("line_items", None, None): 1,
        ("orders", "id", None): 1,
        ("line_items", "order_id", None): 1,
        ("line_items", "quantity", None): 1,
        ("orders", "total_dollars", None): 1,
    }


def test_inner_join_with_aliases_without_as():
    inspector = SqlInspector(
        # How many average orders are there for orders over $500?
        """
        SELECT SUM(li.quantity) FROM orders o INNER JOIN line_items li ON o.id=li.order_id WHERE o.total_dollars > 500;
        """,
        {"orders": ["id", "total_dollars"], "line_items": ["order_id", "quantity"]},
    )
    assert inspector.touches() == {
        ("orders", None, None): 1,
        ("line_items", None, None): 1,
        ("orders", "id", None): 1,
        ("line_items", "order_id", None): 1,
        ("line_items", "quantity", None): 1,
        ("orders", "total_dollars", None): 1,
    }
