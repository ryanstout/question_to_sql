# error is on the snowflake compilation side, we need to adjust the SQL dialect stuff
# https://knolbe.sentry.io/issues/3991381422/?project=4504730283606016&query=is%3Aunresolved&referrer=issue-stream
def test_now():
    # `CURRENT_TIMESTAMP() - INTERVAL '1 month'` should be used instead
    unused_question = "how many text messages did we send last month?"
    unused_query = """
  SELECT
    COUNT(*) AS number_of_text_messages
  FROM text_messages
  WHERE sent_at >= DATE_TRUNC('month', NOW()) - INTERVAL '1 month'
  AND sent_at < DATE_TRUNC('month', NOW());
  """
