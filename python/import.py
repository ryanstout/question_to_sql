import snowflake.connector
from decouple import config

from snowflake.connector.cursor import DictCursor

def snowflake_connection():
  connection_request = snowflake.connector.connect(
    # pull these from the environment
    user=config('SNOWFLAKE_USERNAME'),
    password=config('SNOWFLAKE_PASSWORD'),
    account=config('SNOWFLAKE_ACCOUNT'),
  )

  return connection_request.cursor(cursor_class=DictCursor)

def main(database):
  cursor = snowflake_connection()
  tableList = cursor.execute("SHOW TABLES IN DATABASE " + database)

  # from IPython import embed; embed()

  for table in tableList:
    # for each table,
    breakpoint()

if __name__ == "__main__":
  main(config("SNOWFLAKE_DATABASE"))