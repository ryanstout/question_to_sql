def test_now():
    query = """
  SELECT
    COUNT(*) AS number_of_text_messages
  FROM text_messages
  WHERE sent_at >= DATE_TRUNC('month', NOW()) - INTERVAL '1 month'
  AND sent_at < DATE_TRUNC('month', NOW());
  """
