# Create the schema for a DataSource by querying the embedding indexes and
# deciding which tables, columns, and value hints to include in the prompt.

from prisma.models import User, DataSource, Business, DataSourceTableDescription, DataSourceTableColumn

from schema.full_schema import FullSchema


class SchemaBuilder:
    def __init__(self, db, datasource: DataSource, question: str, schema_builder):
        self.db = db

        # text lines for the schema text
        self.output = []

        # Loop through each table in the datasource
        tables = self.db.datasourcetabledescription.find_many({
            'dataSourceId': datasource.id,
        })

        for table in tables:
            pass


if __name__ == "__main__":
    from utils.connections import Connections

    connections = Connections()
    connections.open()

    db = connections.db

    datasource = db.datasource.find_first()

    SchemaBuilder(db, datasource, "how many orders from Montana?", FullSchema)
