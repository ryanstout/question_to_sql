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

import python.utils as utils
from prisma import Prisma
from python.schema.full_schema import FullSchema
from python.schema.ranker import SCHEMA_RANKING_TYPE, ElementRank

# TODO looks like we cannot set default values on typeddict: https://github.com/python/mypy/issues/6131


class ColumnRank(t.TypedDict):
    column_id: int
    name: str
    hints: t.List[str]


class TableRank(t.TypedDict):
    table_id: int
    fully_qualified_name: str
    columns: t.List[ColumnRank]


TABLE_SCHEMA = t.List[TableRank]


class SchemaBuilder:
    TOKEN_COUNT_LIMIT = 8_000 - 1_024

    def __init__(self, db: Prisma):
        self.db: Prisma = db

    def build(self, ranked_schema: SCHEMA_RANKING_TYPE) -> str:
        return self.generate_sql_from_element_rank(ranked_schema)

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

        rendered_choices = ""

        # remove Nones, empty string, duplicates, and whitespace string from hints
        filtered_hints = set([hint.lower() for hint in hints if hint and hint.strip()])

        if filtered_hints:
            raw_choice_list = repr(filtered_hints)
            # cut out the brackets in the repr render
            rendered_choice_list = raw_choice_list[1:-1]
            rendered_choices = f" -- choices: {rendered_choice_list}"

        # `column1 datatype(length) column_contraint,`
        return f"\t{column.name} {col_type},{rendered_choices}"

    def generate_sql_table_describe(self, table_rank: TableRank) -> str:
        column_sql = []

        for column_rank in table_rank["columns"]:
            column_sql.append(self.generate_column_describe(column_rank["column_id"], column_rank["hints"]))

        rendered_column_sql = "\n".join(column_sql)
        rendered_table_name = utils.sql.unqualified_table_name(table_rank["fully_qualified_name"])

        return f"CREATE TABLE {rendered_table_name} (\n{rendered_column_sql}\n);\n"

    def generate_sql_describe(self, table_ranks: TABLE_SCHEMA) -> str:
        return "\n".join([self.generate_sql_table_describe(table_rank) for table_rank in table_ranks])

    def generate_sql_from_element_rank(self, ranked_schema: SCHEMA_RANKING_TYPE) -> str:
        # we need to transform the ranking schema into a list of table
        table_ranks: t.List[TableRank] = []
        sql = ""

        for element_rank in ranked_schema:
            # first, let's check to see if the new schema is above the token limit
            new_table_sql = self.generate_sql_describe(table_ranks)

            if self.estimate_token_count(new_table_sql) > self.TOKEN_COUNT_LIMIT:
                return sql
            else:
                sql = new_table_sql

            # does the table already exist in table ranks?
            table_rank = next((table_rank for table_rank in table_ranks if table_rank["table_id"] == element_rank["table_id"]), None)

            if not table_rank:
                table = self.db.datasourcetabledescription.find_first(where={"id": element_rank["table_id"]})
                table_rank: TableRank = {
                    "fully_qualified_name": table.fullyQualifiedName,
                    "table_id": table.id,
                    "columns": [],
                }
                table_ranks.append(table_rank)

            if element_rank["column_id"]:
                column_id = element_rank["column_id"]

                # does the column exist in the table_rank object?
                column_rank = next((column_rank for column_rank in table_rank["columns"] if column_rank["column_id"] == column_id), None)

                if column_rank:
                    # add the hint to the column_rank
                    column_rank["hints"].append(element_rank["value_hint"])
                else:
                    # create a new column_rank
                    column = self.db.datasourcetablecolumn.find_first(where={"id": column_id})
                    column_rank: ColumnRank = {
                        "name": column.name,
                        "column_id": column.id,
                        "hints": [element_rank["value_hint"]],
                    }
                    table_rank["columns"].append(column_rank)

        return sql


if __name__ == "__main__":
    from python.utils.connections import Connections

    connections = Connections()
    db = connections.open()

    datasource = db.datasource.find_first()

    # generate via: `poetry run python -m python.schema.ranker "What product sells best in Montana?"`
    ranking_data: t.List[ElementRank] = [
        {"table_id": 8, "column_id": 166, "value_hint": "best-selling", "score": 0.8065115213394165},
        {"table_id": 8, "column_id": 166, "value_hint": "best-selling", "score": 0.8065115213394165},
        {"table_id": 8, "column_id": 166, "value_hint": "best-selling", "score": 0.8065115213394165},
        {"table_id": 9, "column_id": 174, "value_hint": None, "score": 0.7583510875701904},
        {"table_id": 9, "column_id": 174, "value_hint": None, "score": 0.7583510875701904},
        {"table_id": 4, "column_id": 119, "value_hint": None, "score": 0.7519586682319641},
        {"table_id": 4, "column_id": 119, "value_hint": None, "score": 0.7519586682319641},
        {"table_id": 6, "column_id": 155, "value_hint": "Avalara", "score": 0.7475363612174988},
        {"table_id": 6, "column_id": 155, "value_hint": "Avalara", "score": 0.7475363612174988},
        {"table_id": 6, "column_id": 155, "value_hint": "Avalara", "score": 0.7475363612174988},
        {"table_id": 4, "column_id": 113, "value_hint": None, "score": 0.7455527782440186},
        {"table_id": 6, "column_id": 152, "value_hint": None, "score": 0.7443681359291077},
        {"table_id": 4, "column_id": 120, "value_hint": None, "score": 0.7443681359291077},
        {"table_id": 1, "column_id": 6, "value_hint": None, "score": 0.7430565357208252},
        {"table_id": 8, "column_id": 167, "value_hint": None, "score": 0.7430565357208252},
        {"table_id": 6, "column_id": 154, "value_hint": None, "score": 0.7430565357208252},
        {"table_id": 4, "column_id": 123, "value_hint": None, "score": 0.7430565357208252},
        {"table_id": 1, "column_id": 6, "value_hint": None, "score": 0.7430565357208252},
        {"table_id": 10, "column_id": 175, "value_hint": None, "score": 0.7422063946723938},
        {"table_id": 10, "column_id": 175, "value_hint": None, "score": 0.7422063946723938},
        {"table_id": 6, "column_id": 159, "value_hint": None, "score": 0.7405303716659546},
        {"table_id": 3, "column_id": 97, "value_hint": "percentage", "score": 0.7401782274246216},
        {"table_id": 3, "column_id": 97, "value_hint": "percentage", "score": 0.7401782274246216},
        {"table_id": 3, "column_id": 97, "value_hint": "percentage", "score": 0.7401782274246216},
        {"table_id": 1, "column_id": 2, "value_hint": None, "score": 0.7391866445541382},
        {"table_id": 4, "column_id": 110, "value_hint": None, "score": 0.7382106781005859},
        {"table_id": 6, "column_id": 157, "value_hint": None, "score": 0.7376145124435425},
        {"table_id": 10, "column_id": 176, "value_hint": None, "score": 0.734853982925415},
        {"table_id": 8, "column_id": 166, "value_hint": "price-asc", "score": 0.7295647859573364},
        {"table_id": 8, "column_id": 166, "value_hint": "manual", "score": 0.7221354246139526},
        {"table_id": 8, "column_id": 166, "value_hint": "created-desc", "score": 0.7215535640716553},
        {"table_id": 9, "column_id": None, "value_hint": None, "score": 0.7204369306564331},
        {"table_id": 8, "column_id": 172, "value_hint": "web", "score": 0.7185894250869751},
        {"table_id": 8, "column_id": 172, "value_hint": "web", "score": 0.7185894250869751},
        {"table_id": 8, "column_id": 170, "value_hint": "shogun", "score": 0.7158838510513306},
        {"table_id": 8, "column_id": 170, "value_hint": "shogun", "score": 0.7158838510513306},
        {"table_id": 5, "column_id": None, "value_hint": None, "score": 0.7091584205627441},
        {"table_id": 2, "column_id": None, "value_hint": None, "score": 0.7083749175071716},
        {"table_id": 2, "column_id": 26, "value_hint": None, "score": 0.7042477130889893},
        {
            "table_id": 2,
            "column_id": 26,
            "value_hint": "Engraving: Always Faithful, Always Strong\nFont: Script\nRed Filled Engraving",
            "score": 0.7008172273635864,
        },
        {"table_id": 3, "column_id": 97, "value_hint": "fixed_amount", "score": 0.6898645758628845},
        {"table_id": 7, "column_id": None, "value_hint": None, "score": 0.6895037889480591},
    ]

    print(SchemaBuilder(db).build(ranking_data))
