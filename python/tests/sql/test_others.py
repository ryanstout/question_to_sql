from python.sql.sql_inspector import SqlInspector


def test_sum_propigation():
    inspector = SqlInspector(
        """
        SELECT SUM(col1) as col1_sum  FROM table1;
        """,
        {"table1": {"name": "table1", "columns": {"col1": {"name": "col1"}, "col2": {"name": "col2"}}}},
    )
    assert inspector.touches() == {("table1", None, None): 1, ("table1", "col1", None): 2}

    inspector = SqlInspector(
        """
        SELECT SUM(col1) FROM table1;
        """,
        {"table1": {"name": "table1", "columns": {"col1": {"name": "col1"}, "col2": {"name": "col2"}}}},
    )
    assert inspector.touches() == {("table1", None, None): 1, ("table1", "col1", None): 1}


# def test_where_clause_equals_string():
#     inspector = SqlInspector(
#         """
#         SELECT * FROM orders WHERE state = 'Montana';
#         """,
#         {'orders': {'name': 'orders', 'columns': {'id': {'name': 'id'}, 'total_dollars': {'name': 'total_dollars'}}}},
#     )
#     assert inspector.touches() == [("orders", "state")]
#     # assert inspector.values == [("orders", "state", "Montana")]


# def test_sql_extract_table_and_columns2():
#     inspector = SqlInspector(
#         """
#     SELECT
#   COUNT(*) AS orders_per_customer,
#   COUNT(DISTINCT customer_id) AS customers_per_order,
#   CAST(COUNT(DISTINCT customer_id) AS FLOAT) / COUNT(*) AS customers_per_order_avg,
#   pr.vendor
# FROM "ORDER"
# JOIN ORDER_LINE
#   ON ORDER_LINE.order_id = "ORDER".id
# JOIN PRODUCT_VARIANT
#   ON PRODUCT_VARIANT.id = ORDER_LINE.variant_id
# JOIN PRODUCT as pr
#   ON pr.id = PRODUCT_VARIANT.product_id
# WHERE
#   pr.vendor = 'Dayspring Pens' AND
#   customers_per_order > 5
#     """
#     )
#     assert inspector == []
