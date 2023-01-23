# Create the schema for a DataSource by querying the embedding indexes and
# deciding which tables, columns, and value hints to include in the prompt.

from prisma.models import User, DataSource, Business, DataSourceTableDescription, DataSourceTableColumn


class SchemaBuilder:
    def __init__(self, db, datasource: DataSource, question: str):
        self.db = db

        # text lines for the schema text
        self.output = []

        # Loop through each table in the datasource
        tables = self.db.datasourcetabledescription.find_many({
            'dataSourceId': datasource.id,
        }

        for table in tables:
