import pytest

from python.sql.sql_table_and_columns import table_and_columns_for_sql


def test_sql_extract_table_and_columns():
    # table_and_cols = table_and_columns_for_sql("SELECT name FROM orders;")
    # assert table_and_cols == [["orders", "name"]]

    table_and_cols = table_and_columns_for_sql(
        """
    SELECT
  COUNT(*) AS days_with_more_than_10_orders
FROM (
  SELECT
    order_total as ot,
    COUNT(*) AS orders_per_day,
    EXTRACT(DAY FROM created_at) AS day
  FROM "ORDER"
  GROUP BY
    day
  HAVING
    COUNT(*) > 10
);
"""
    )
    assert table_and_cols == []
