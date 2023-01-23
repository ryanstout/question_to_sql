# A helper that builds the full schema with a cap on the number of value hints
# for string fields. Builds the same data structure as ./ranker.py

class FullSchema:
    def build(self, db):
        schema = {}

        # Loop through each table in the datasource
        tables = db.datasourcetabledescription.find_many({})

        for table in tables:
            table_name = table['name']

            # Loop through each column in the table
            columns = db.datasourcetabledescription.find_many({
                'dataSourceId': table['dataSourceId'],
            })

            schema[table_name] = {}

            for column in columns:
                column_name = column['name']

                # Get the value hints for the column
                value_hints = []

                schema[table_name][column_name] = value_hints

        return schema
