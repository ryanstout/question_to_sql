from python.sql.sql_inspector import SqlInspector
from python.sql.types import SimpleSchema

BASIC_SCHEMA_STRUCTURE: SimpleSchema = {
    "table1": {"name": "table1", "columns": {"col1": {"name": "col1"}, "col2": {"name": "col2"}}}
}


def test_static_alias():
    inspector = SqlInspector(
        """
        SELECT 'unsure' AS user_name;
        """,
        BASIC_SCHEMA_STRUCTURE,
    )

    assert inspector.touches() == {}


def test_string_concat():
    inspector = SqlInspector(
        """
        SELECT 'a' || 'b' AS col1;
        """,
        BASIC_SCHEMA_STRUCTURE,
    )

    assert inspector.touches() == {}


# TODO this is failing!
def test_complex_string_concat():
    inspector = SqlInspector(
        """
        SELECT
            COUNT(*) AS orders_per_customer,
            customer.first_name || ' ' || customer.last_name AS full_name
        FROM "order"
        JOIN customer
            ON customer.id = "order".customer_id
        GROUP BY
            customer.first_name,
            customer.last_name
        ORDER BY
            orders_per_customer DESC
        LIMIT 5;
        """,
        {
            "order": {
                "name": "order",
                "columns": {
                    "customer_id": {"name": "customer_id"},
                },
            },
            "customer": {
                "name": "customer",
                "columns": {
                    "id": {"name": "id"},
                    "first_name": {"name": "first_name"},
                    "last_name": {"name": "last_name"},
                },
            },
        },
    )

    assert inspector.touches() == {
        ("order", None, None): 1,
        ("customer", None, None): 1,
        ("customer", "id", None): 1,
        ("order", "customer_id", None): 1,
        ("customer", "first_name", None): 3,
        ("customer", "last_name", None): 3,
    }


def test_sum_propagation():
    inspector = SqlInspector(
        """
        SELECT SUM(col1) as col1_sum  FROM table1;
        """,
        BASIC_SCHEMA_STRUCTURE,
    )
    assert inspector.touches() == {("table1", None, None): 1, ("table1", "col1", None): 2}

    inspector = SqlInspector(
        """
        SELECT SUM(col1) FROM table1;
        """,
        BASIC_SCHEMA_STRUCTURE,
    )
    assert inspector.touches() == {("table1", None, None): 1, ("table1", "col1", None): 1}


# https://knolbe.sentry.io/issues/4002618863/?project=4504730283606016&query=is%3Aunresolved&referrer=issue-stream
def test_unsure():
    query = """
    SELECT 'unsure'
    """


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
