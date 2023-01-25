import snowflake.connector
from decouple import config
from snowflake.connector.cursor import DictCursor

from prisma import Prisma


class Connections:
    def open(self):
        self.db = Prisma()
        self.db.connect()

        # TODO this will need to be pulled from the datasource
        self.snowflake_connection = snowflake.connector.connect(
            # pull these from the environment
            user=config("SNOWFLAKE_USERNAME"),
            password=config("SNOWFLAKE_PASSWORD"),
            account=config("SNOWFLAKE_ACCOUNT"),
        )

        return self.db

    def snowflake_cursor(self):
        cursor = self.snowflake_connection.cursor(cursor_class=DictCursor)

        # TODO: Move this into a DataSource
        cursor.execute("use warehouse COMPUTE_WH;")

        return cursor

    def close(self):
        self.db.disconnect()
        self.snowflake_connection.close()
