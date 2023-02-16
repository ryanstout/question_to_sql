from pprint import pprint

import pytest
from rich import print

from python.sql.exceptions import ColumnNotFoundError, TableNotFoundError
from python.sql.sql_inspector import SqlInspector


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

    simple_schema = {
        "order": ["id", "created_at"],
        "order_line": ["order_id", "variant_id"],
        "product_variant": ["id", "product_id"],
        "product": ["id", "title"],
    }

    inspector = SqlInspector(query, simple_schema)
