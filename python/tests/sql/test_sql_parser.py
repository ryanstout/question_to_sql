from python.sql.sql_parser import SqlParser


def test_now_replacement():
    """Test that NOW() is replaced with CURRENT_TIMESTAMP"""
    sql = """SELECT
  COUNT(DISTINCT o1.id) AS same_brand_orders,
  COUNT(DISTINCT o2.id) AS total_repeat_orders,
  (
    COUNT(DISTINCT o1.id) * 1.0 / COUNT(DISTINCT o2.id)
  ) * 100 AS likelihood_same_brand
FROM "ORDER" AS o1
JOIN "ORDER" AS o2
  ON o1.customer_id = o2.customer_id
  AND o1.id <> o2.id
  AND o1.created_at < o2.created_at
  AND o1.created_at >= (
    NOW() - INTERVAL '2 YEARS'
  )
JOIN order_line AS ol1
  ON ol1.order_id = o1.id
JOIN order_line AS ol2
  ON ol2.order_id = o2.id
JOIN product_variant AS pv1
  ON pv1.id = ol1.variant_id
JOIN product_variant AS pv2
  ON pv2.id = ol2.variant_id
JOIN product AS p1
  ON p1.id = pv1.product_id
JOIN product AS p2
  ON p2.id = pv2.product_id
WHERE
  p1.vendor = p2.vendor LIMIT 100"""

    replaced = SqlParser().string_translations(sql)
    print("REPLACED: ", replaced)
    # assert  == expected
