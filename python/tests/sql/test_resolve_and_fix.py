from python.sql.sql_resolve_and_fix import SqlResolveAndFix
from python.tests.sql.fixtures.pens_schema import pens_schema


def test_resolve_and_fix():

    result = SqlResolveAndFix().run(
        """
    SELECT COUNT(*) AS orders_per_product,
  PRODUCT.title
FROM "ORDER"
JOIN ORDER_LINE
  ON ORDER_LINE.order_id = "ORDER".id
JOIN PRODUCT_VARIANT
  ON PRODUCT_VARIANT.id = ORDER_LINE.variant_id
JOIN PRODUCT
  ON PRODUCT.id = PRODUCT_VARIANT.product_id
GROUP BY
  PRODUCT.title
ORDER BY
orders_per_product DESC NULLS FIRST LIMIT 10;
""",
        pens_schema,
    )

    assert (
        result
        == """SELECT\n  COUNT(*) AS orders_per_product,\n  PRODUCT.title\nFROM "ORDER"\nJOIN ORDER_LINE\n  ON ORDER_LINE.order_id = "ORDER".id\nJOIN PRODUCT_VARIANT\n  ON PRODUCT_VARIANT.id = ORDER_LINE.variant_id\nJOIN PRODUCT\n  ON PRODUCT.id = PRODUCT_VARIANT.product_id\nGROUP BY\n  PRODUCT.title\nORDER BY\n  orders_per_product DESC NULLS FIRST\nLIMIT 10"""
    )


def test_fix_case():
    # print(pens_schema["order"])
    result = SqlResolveAndFix().run(
        """SELECT
  COUNT(*) AS total_orders
FROM "order"
""",
        pens_schema,
    )
    assert result == 'SELECT\n  COUNT(*) AS total_orders\nFROM "ORDER"'

    result = SqlResolveAndFix().run("""SELECT order.id, total_price FROM order LIMIT 5;""", pens_schema)
    assert result == """SELECT\n  "ORDER".id,\n  total_price\nFROM "ORDER"\nLIMIT 5"""


# def test_ambigious_column():
#     query = """SELECT
#     COUNT(*) AS orders_per_product,
#     product.title
# FROM "order"
# JOIN order_line
#     ON order_line.order_id = "order".id
# JOIN product_variant
#     ON product_variant.id = order_line.variant_id
# JOIN product
#     ON product.id = product_variant.product_id
# WHERE EXTRACT(DOW FROM created_at) = 2
# GROUP BY
#     product.title
# ORDER BY
# orders_per_product DESC NULLS FIRST
# LIMIT 10;"""


def test_vendor_issue():
    query = """SELECT vendor, COUNT(*) AS num_same_vendor_orders, COUNT(*) * 1.0 / total_repeat_orders AS likelihood
FROM (
    SELECT o.id AS order_id, p.vendor
    FROM order o
    JOIN order_line ol ON o.id = ol.order_id
    JOIN product p ON ol.product_id = p.id
    WHERE o.customer_id IN (
        SELECT customer_id
        FROM order
        WHERE created_at >= DATEADD('year', -2, CURRENT_TIMESTAMP())
        GROUP BY customer_id
        HAVING COUNT(*) > 1
    )
) AS repeat_orders
JOIN (
    SELECT COUNT(*) AS total_repeat_orders
    FROM order
    WHERE customer_id IN (
        SELECT customer_id
        FROM order
        WHERE created_at >= DATEADD('year', -2, CURRENT_TIMESTAMP())
        GROUP BY customer_id
        HAVING COUNT(*) > 1
    )
) AS total_orders
GROUP BY vendor, total_repeat_orders
ORDER BY likelihood DESC;"""

    SqlResolveAndFix().run(query, pens_schema)


def test_subquery_as_passthrough():
    query = """SELECT customer_id
FROM order
JOIN (
    SELECT customer.id AS customer_id, SUM(order.total_price) AS customer_total_spent
    FROM customer
    JOIN order ON customer.id = order.customer_id
    LIMIT 15
) AS top_customers ON order.customer_id = top_customers.customer_id
"""

    SqlResolveAndFix().run(query, pens_schema)


def test_order_id_not_found():
    query = """SELECT
  COUNT(*) AS orders_per_month,
  EXTRACT(MONTH FROM "order".created_at) AS month,
  EXTRACT(YEAR FROM "order".created_at) AS year
FROM "order"
JOIN order_line
  ON order_line.order_id = "order".id
JOIN product_variant
  ON product_variant.id = order_line.variant_id
JOIN product
  ON product.id = product_variant.product_id
WHERE
  product.title = 'Cross Bailey Fountain Pen - Black Lacquer'
  AND "order".created_at >= NOW() - INTERVAL '5 years'
  AND EXISTS (
    SELECT *
    FROM order_line
    JOIN product_variant
      ON product_variant.id = order_line.variant_id
    JOIN product
      ON product.id = product_variant.product_id
    WHERE
      product.title = 'Cross Bailey Medalist Ballpoint Pen'
      AND order_line.order_id = "order".id
  )
GROUP BY
  month,
  year
ORDER BY
  orders_per_month DESC NULLS FIRST;"""

    SqlResolveAndFix().run(query, pens_schema)


def test_where_can_access_select_expressoins():
    query = """SELECT
  EXTRACT(MONTH FROM "order".created_at) AS month,
FROM "order"
WHERE
  month = 1;"""

    SqlResolveAndFix().run(query, pens_schema)


def test_missing_month1():
    query = """SELECT
  EXTRACT(MONTH FROM "order".created_at) AS month,
  EXTRACT(YEAR FROM "order".created_at) AS year
FROM "order"
WHERE
    month = 1
;"""

    SqlResolveAndFix().run(query, pens_schema)


def test_missing_month():
    query = """SELECT
  COUNT(*) AS order_count,
  EXTRACT(MONTH FROM "order".created_at) AS month,
  EXTRACT(YEAR FROM "order".created_at) AS year
FROM "order"
JOIN order_line
  ON order_line.order_id = "order".id
JOIN product_variant
  ON product_variant.id = order_line.variant_id
JOIN product
  ON product.id = product_variant.product_id
WHERE
  product.title = 'Cross Classic Century Chrome Ballpoint & Fountain Pen Set'
  AND (
    (month = 1 AND year = 2023)
    OR (month = 12 AND year = 2022)
    OR (month = 1 AND year = 2022)
    OR (month = 12 AND year = 2021)
  )
GROUP BY
  month,
  year
ORDER BY
  year DESC,
  month DESC;"""

    SqlResolveAndFix().run(query, pens_schema)
