# Create the schema for a DataSource by querying the embedding indexes and
# deciding which tables, columns, and value hints to include in the prompt.

import re
import typing as t

import tiktoken
from prisma.models import (
    Business,
    DataSource,
    DataSourceTableColumn,
    DataSourceTableDescription,
    User,
)

from prisma import Prisma
from python.schema.full_schema import FullSchema
from python.schema.ranker import SCHEMA_RANKING_TYPE


class SchemaBuilder:
    TOKEN_COUNT_LIMIT = 8_000 - 1_024

    def __init__(self, db: Prisma):
        self.db: Prisma = db

    def build(self, ranked_schema: SCHEMA_RANKING_TYPE):
        return self.generate_sql(ranked_schema)

    def estimate_token_count(self, text: str) -> int:
        enc = tiktoken.get_encoding("gpt2")
        return len(enc.encode(text))

    def generate_column_describe(self, column_id: int, hints: t.List[str]) -> str:
        # TODO should we filter by kind?
        column = self.db.datasourcetablecolumn.find_first(where={"id": column_id})
        if column is None:
            raise Exception(f"column not found {column_id}")

        if column.type == "VARCHAR(256)":
            col_type = "VARCHAR"
        elif re.search("^TIMESTAMP_TZ", column.type):
            col_type = "TIMESTAMP"
        else:
            col_type = column.type

        # `column1 datatype(length) column_contraint,`
        return f""""
        {column.name} {col_type}, -- choices: {", ".join(hints)}
        """

    def generate_sql_table_describe(self, ranked_schema: SCHEMA_RANKING_TYPE, table_id: int) -> str:
        table = self.db.datasourcetabledescription.find_first(where={"id": table_id})
        column_sql = []

        for column_id in ranked_schema[table_id].keys():
            column_sql.append(self.generate_column_describe(column_id, ranked_schema[table_id][column_id]))

        rendered_column_sql = ", \n".join(column_sql)
        f"""
        CREATE TABLE {table.fullyQualifiedName} (
            {rendered_column_sql}
        );
        """

    def generate_sql(self, ranked_schema: SCHEMA_RANKING_TYPE):
        sql = ""

        for table_id in ranked_schema.keys():
            new_table_sql = self.generate_sql_table_describe(ranked_schema, table_id)

            if self.estimate_token_count(sql + new_table_sql) > self.TOKEN_COUNT_LIMIT:
                return sql
            else:
                sql += new_table_sql


if __name__ == "__main__":
    from python.utils.connections import Connections

    connections = Connections()
    db = connections.open()

    datasource = db.datasource.find_first()

    ranking_data = {
        26: {424: []},
        25: {401: [], 411: []},
        19: {340: []},
        4: {124: []},
        23: {371: [], 370: [], 365: ["FedEx"]},
        18: {273: [], 276: [], 283: [], 267: ["USD"]},
        36: {},
        37: {},
        5: {139: ["ups_shipping", "shopify", "fedex", "APC Postal Logistics"], 138: [], None: []},
        27: {427: []},
        24: {385: [], 386: [], 379: ["delivered", "in_transit", "out_for_delivery", "confirmed"]},
        12: {223: []},
        20: {353: []},
        6: {163: []},
        2: {36: ["USD"]},
        54: {},
        53: {},
        30: {},
        47: {},
        55: {},
        10: {},
        22: {362: ["Cross Drop Ship", "Howard Miller Drop Ship"]},
        15: {241: ["USD"]},
        8: {170: ["web"]},
    }

    print(SchemaBuilder(db).build(ranking_data))
