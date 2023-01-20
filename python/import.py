# Imports the schema and metadata from the snowflake database to the
# local database.

from snowflake.connector.cursor import DictCursor
import snowflake.connector
from decouple import config
import sys
from prisma import Prisma
from prisma.models import User, DataSource, Business
from prisma.enums import DataSourceType


class Import():
    def __init__(self, user_id, database):
        self.db = Prisma()
        self.db.connect()

        user = self.db.user.find_unique(where={'id': int(user_id)})
        if user is None:
            raise Exception("User not found")

        business = self.find_or_create_business(user)
        datastore = self.find_or_create_datasource(business)

        # Dump the data from each table into the database
        cursor = self.snowflake_connection()
        tableList = cursor.execute("SHOW TABLES IN DATABASE " + database)

        # from IPython import embed; embed()

        for table in tableList:
            from IPython import embed
            embed()
            # for each table,
            # breakpoint()

    def snowflake_connection(self):
        connection_request = snowflake.connector.connect(
            # pull these from the environment
            user=config('SNOWFLAKE_USERNAME'),
            password=config('SNOWFLAKE_PASSWORD'),
            account=config('SNOWFLAKE_ACCOUNT'),
        )

        return connection_request.cursor(cursor_class=DictCursor)

    def find_or_create_business(self, user):
        # Create and assign a business if there isn't one
        if user.business is None:
            business = self.db.business.create(data={
                'name': config("SNOWFLAKE_DATABASE")
            })
            self.db.user.update(
                data={'businessId': business.id}, where={'id': user.id})

            return business

        else:
            return user.business

    def find_or_create_datasource(self, business: Business):
        # Temp method to create a datasource
        first_source = self.db.datasource.find_first(
            where={'businessId': business.id})

        if first_source is not None:
            return first_source

        db_name = config("SNOWFLAKE_DATABASE")
        return self.db.datasource.create(data={
            'name': f"Snowflake for {db_name}",
            'businessId': int(business.id),
            'credentials': '{}',
            'type': DataSourceType.SNOWFLAKE,
        })


if __name__ == "__main__":
    Import(sys.argv[1], config("SNOWFLAKE_DATABASE"))
