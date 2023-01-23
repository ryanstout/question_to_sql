from schema.schema_builder import SchemaBuilder
from python.utils.connections import Connections


class QuestionToSql:
    def __init__(self):
        self.connections = Connections()
        self.connections.open()

        self.db = self.connections.db

    def convert(self, question: str):
        schema = SchemaBuilder(self.db, question).build()
