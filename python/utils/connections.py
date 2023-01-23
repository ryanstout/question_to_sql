from prisma import Prisma
from snowflake.connector.cursor import DictCursor
import snowflake.connector
from decouple import config


class Connections:
    def open(self):
        self.db = Prisma()
        self.db.connect()

        self.snowflake_connection = snowflake.connector.connect(
            # pull these from the environment
            user=config('SNOWFLAKE_USERNAME'),
            password=config('SNOWFLAKE_PASSWORD'),
            account=config('SNOWFLAKE_ACCOUNT'),
        )

    def snowflake_cursor(self):
        return self.snowflake_connection.cursor(cursor_class=DictCursor)

    def close(self):
        self.db.disconnect()
        self.snowflake_connection.close()
