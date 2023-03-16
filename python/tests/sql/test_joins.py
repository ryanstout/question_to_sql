from python.sql.sql_inspector import SqlInspector


def test_inner_join():
    inspector = SqlInspector(
        """
        SELECT t1.col1, t2.col2 FROM table1 as t1 INNER JOIN table2 as t2 ON t1.col1 = t2.col2;
        """,
        {
            "table1": {"name": "table1", "columns": {"col1": {"name": "col1"}, "col4": {"name": "col4"}}},
            "table2": {"name": "table2", "columns": {"col2": {"name": "col2"}, "col3": {"name": "col3"}}},
        },
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
        {
            "orders": {"name": "orders", "columns": {"id": {"name": "id"}, "total_dollars": {"name": "total_dollars"}}},
            "line_items": {
                "name": "line_items",
                "columns": {"order_id": {"name": "order_id"}, "quantity": {"name": "quantity"}},
            },
        },
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
        {
            "orders": {"name": "orders", "columns": {"id": {"name": "id"}, "total_dollars": {"name": "total_dollars"}}},
            "line_items": {
                "name": "line_items",
                "columns": {"order_id": {"name": "order_id"}, "quantity": {"name": "quantity"}},
            },
        },
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
        {
            "orders": {"name": "orders", "columns": {"id": {"name": "id"}, "total_dollars": {"name": "total_dollars"}}},
            "line_items": {
                "name": "line_items",
                "columns": {"order_id": {"name": "order_id"}, "quantity": {"name": "quantity"}},
            },
        },
    )
    assert inspector.touches() == {
        ("orders", None, None): 1,
        ("line_items", None, None): 1,
        ("orders", "id", None): 1,
        ("line_items", "order_id", None): 1,
        ("line_items", "quantity", None): 1,
        ("orders", "total_dollars", None): 1,
    }


# https://knolbe.sentry.io/issues/3991381422/?project=4504730283606016&query=is%3Aunresolved&referrer=issue-stream
def test_ambigious_columns():
    # TODO fails because created at is ambigious
    #      this is on daniel's DB
    sql = """
    SELECT
  COUNT(*) AS classic_century_sold
FROM "ORDER"
JOIN order_line
  ON order_line.order_id = "ORDER".id
JOIN product
  ON product.id = order_line.product_id
WHERE
  product.title ILIKE '%Cross Classic Century%'
  AND created_at > CURRENT_TIMESTAMP() - INTERVAL '1 year'
    """

