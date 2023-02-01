import pytest

from python.sql.sql_table_and_columns import SqlTouchPoints, table_and_columns_for_sql

# def test_sql_extract_table_and_columns():
#     # table_and_cols = table_and_columns_for_sql("SELECT name FROM orders;")
#     # assert table_and_cols == [["orders", "name"]]

#     # table_and_cols = table_and_columns_for_sql(
#     table_and_cols = SqlTouchPoints().extract(
#         """
#     SELECT
#   COUNT(*) AS days_with_more_than_10_orders,
# FROM (
#   SELECT
#     order_total as ot,
#     COUNT(*) AS orders_per_day,
#     EXTRACT(DAY FROM created_at) AS day
#   FROM "ORDER"
#   GROUP BY
#     day
#   HAVING
#     COUNT(*) > 10
# );
# """
#     )
#     assert table_and_cols == []


def test_sql_extract_table_and_columns2():
    table_and_cols = SqlTouchPoints().extract(
        """
    SELECT
  COUNT(*) AS orders_per_customer,
  COUNT(DISTINCT customer_id) AS customers_per_order,
  CAST(COUNT(DISTINCT customer_id) AS FLOAT) / COUNT(*) AS customers_per_order_avg,
  pr.vendor
FROM "ORDER"
JOIN ORDER_LINE
  ON ORDER_LINE.order_id = "ORDER".id
JOIN PRODUCT_VARIANT
  ON PRODUCT_VARIANT.id = ORDER_LINE.variant_id
JOIN PRODUCT as pr
  ON pr.id = PRODUCT_VARIANT.product_id
WHERE
  pr.vendor = 'Dayspring Pens' AND
  customers_per_order > 5
    """
    )
    assert table_and_cols == []
