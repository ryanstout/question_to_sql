from python.sql.sql_inspector import SqlInspector
from python.sql.sql_parser import SqlParser
from python.sql.types import SimpleSchema
from python.tests.sql.fixtures.pens_schema import pens_schema


def test_complex1():
    query = """
    SELECT DISTINCT
  COUNT(*) AS orders_per_product,
  product.title
FROM "order"
JOIN order_line
  ON order_line.order_id = "order".id
JOIN product_variant
  ON product_variant.id = order_line.variant_id
JOIN product
  ON product.id = product_variant.product_id
GROUP BY
  product.title
ORDER BY
orders_per_product DESC NULLS FIRST
LIMIT 10;"""

    simple_schema: SimpleSchema = {
        "order": {"name": "order", "columns": {"id": {"name": "id"}, "created_at": {"name": "created_at"}}},
        "order_line": {
            "name": "order_line",
            "columns": {"order_id": {"name": "order_id"}, "variant_id": {"name": "variant_id"}},
        },
        "product_variant": {
            "name": "product_variant",
            "columns": {"id": {"name": "id"}, "product_id": {"name": "product_id"}},
        },
        "product": {"name": "product", "columns": {"id": {"name": "id"}, "title": {"name": "title"}}},
    }

    SqlInspector(query, simple_schema)


def test_over_and_partition_complex2():
    query = """
  SELECT 
    EXTRACT(YEAR FROM created_at) AS year,
    EXTRACT(QUARTER FROM created_at) AS quarter,
    SUM(total_price) AS total_sales,
    SUM(total_price) / LAG(SUM(total_price)) OVER (PARTITION BY EXTRACT(YEAR FROM created_at) ORDER BY EXTRACT(QUARTER FROM created_at)) - 1 AS percent_change
FROM "order"
GROUP BY
    year,
    quarter
ORDER BY
    year,
    quarter;
    """

    SqlInspector(query, pens_schema)


def test_case_fixup():
    query = """
  SELECT
  MIN(created_at)
FROM order
JOIN customer_address
  ON customer_address.customer_id = order.customer_id
WHERE
  customer_address.province = 'Washington';
  """

    result_query = """SELECT MIN(created_at) FROM ORDER JOIN customer_address ON customer_address.customer_id = ORDER.customer_id WHERE customer_address.province = 'Washington'"""

    ast = SqlParser().run(query)
    SqlInspector(ast, pens_schema)
    assert ast.sql() == result_query


def test_value_lookup1():
    sql = """SELECT
  COUNT(*) AS paid_orders_last_week
FROM order
WHERE
  financial_status = 'paid'
  AND created_at >= CURRENT_TIMESTAMP() - INTERVAL '7 days'
  AND billing_address_province IN ('California', 'Oregon', 'Washington')"""

    inspector = SqlInspector(sql, pens_schema)
    print(inspector.touches())
    assert inspector.touches() == {
        ("order", None, None): 1,
        ("order", "financial_status", None): 1,
        ("order", "financial_status", "paid"): 1,
        ("order", "created_at", None): 1,
        ("order", "billing_address_province", None): 1,
    }
