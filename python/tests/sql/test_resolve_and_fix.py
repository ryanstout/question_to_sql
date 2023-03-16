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
