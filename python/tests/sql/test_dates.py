# error is on the snowflake compilation side, we need to adjust the SQL dialect stuff
# https://knolbe.sentry.io/issues/3991381422/?project=4504730283606016&query=is%3Aunresolved&referrer=issue-stream
from python.sql.sql_inspector import SqlInspector
from python.tests.sql.fixtures.pens_schema import pens_schema


def test_now():
    # `CURRENT_TIMESTAMP() - INTERVAL '1 month'` should be used instead
    unused_question = "how many text messages did we send last month?"
    unused_query = """
  SELECT
    COUNT(*) AS fufilled
  FROM fulfillment
  WHERE created_at >= DATE_TRUNC('month', NOW()) - INTERVAL '1 month'
  AND created_at < DATE_TRUNC('month', NOW());
  """

    inspector = SqlInspector(query, pens_schema)
    assert inspector.touches() == {
        ("fulfillment", None, None): 1,
        ("fulfillment", "created_at", None): 2,
    }


def test_dateadd():
    query = """
    SELECT
  COUNT(*) AS orders_last_6_months
FROM "order"
WHERE
  created_at >= DATEADD(MONTH, -6, NOW());
    """

    inspector = SqlInspector(query, pens_schema)
    assert inspector.touches() == {
        ("order", None, None): 1,
        ("order", "created_at", None): 1,
    }


def test_extract():
    query = """
    SELECT COUNT(*) AS orders_per_month,
    EXTRACT(MONTH FROM "ORDER".created_at) AS month
    FROM "ORDER";
    """

    inspector = SqlInspector(query, pens_schema)
    print(inspector.touches())
    assert inspector.touches() == {
        ("ORDER", None, None): 1,
        ("ORDER", "created_at", None): 2,
    }
