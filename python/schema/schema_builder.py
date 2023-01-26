# Create the schema for a DataSource by querying the embedding indexes and
# deciding which tables, columns, and value hints to include in the prompt.

# always include ID, include ID first, NOT NULL annotations, all `_id` columns on all tables that we include
# order the columns naturally

from python.setup import log

import re
import time
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
from python.schema.ranker import SCHEMA_RANKING_TYPE, ElementRank, Ranker
from python.sql.post_transform import PostTransform

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


# TODO move to a generic utils
def estimate_token_count(text: str) -> int:
    enc = tiktoken.get_encoding("gpt2")
    token_count = len(enc.encode(text))
    return token_count


class SchemaBuilder:
    TOKEN_COUNT_LIMIT = 7_000 - 1_024

    def __init__(self, db: Prisma):
        self.db: Prisma = db
        self.cached_columns = {}

    def build(self, ranked_schema: SCHEMA_RANKING_TYPE) -> str:
        return self.generate_sql_from_element_rank(ranked_schema)

    def generate_column_describe(self, column_id: int, hints: t.List[str]) -> str:
        # TODO should we filter by kind?
        column = self.cached_columns.get(column_id, None)

        # not caching the columns was creating a massive slowdown in schema generation
        if not column:
            column = self.cached_columns[column_id] = self.db.datasourcetablecolumn.find_first(where={"id": column_id})

        if column is None:
            raise Exception(f"column not found {column_id}")

        if column.type == "VARCHAR(256)":
            col_type = "VARCHAR"
        elif re.search("^TIMESTAMP_TZ", column.type):
            col_type = "TIMESTAMP"
        elif re.search("^VARIANT", column.type):
            return None  # skip this column
        elif re.search("^NUMBER", column.type):
            if PostTransform.in_dialect == "postgres":
                col_type = column.type.replace("NUMBER", "NUMERIC")
            else:
                # Don't replace it if it's snowflake
                col_type = column.type
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
        return f"\t{column.name} {col_type},{rendered_choices}".lower()

    def generate_sql_table_describe(self, table_rank: TableRank) -> str:
        column_sql = []

        for column_rank in table_rank["columns"]:
            column_description = self.generate_column_describe(column_rank["column_id"], column_rank["hints"])
            if column_description is not None:
                column_sql.append(column_description)

        rendered_column_sql = "\n".join(column_sql)
        rendered_table_name = utils.sql.unqualified_table_name(table_rank["fully_qualified_name"]).lower()

        return f"CREATE TABLE {rendered_table_name} (\n{rendered_column_sql}\n);\n"

    def generate_sql_describe(self, table_ranks: TABLE_SCHEMA) -> str:
        return "\n".join([self.generate_sql_table_describe(table_rank) for table_rank in table_ranks])

    def create_table_rank(self, tableId: int) -> TableRank:
        table = self.db.datasourcetabledescription.find_first(where={"id": tableId})

        # we want to include the primary key and all foreign keys by default as columns
        id_columns = self.db.datasourcetablecolumn.find_many(
            where={
                "AND": [
                    {"dataSourceTableDescriptionId": tableId},
                    {
                        "OR": [
                            {
                                "name": {
                                    # TODO should allow for endsWith instead!
                                    "endswith": "_ID",
                                }
                            },
                            {"name": "ID"},
                        ]
                    },
                ],
            }
        )

        default_id_columns = [
            self.create_column_rank(ElementRank(table_id=tableId, column_id=column.id, value_hint=None, score=0.0)) for column in id_columns
        ]

        return {
            "fully_qualified_name": table.fullyQualifiedName,
            "table_id": table.id,
            "columns": default_id_columns,
        }

    def create_column_rank(self, column_rank: ElementRank) -> ColumnRank:
        column = self.db.datasourcetablecolumn.find_first(where={"id": column_rank["column_id"]})

        return {
            "name": column.name,
            "column_id": column.id,
            "hints": [column_rank["value_hint"]],
        }

    def generate_sql_from_element_rank(self, ranked_schema: SCHEMA_RANKING_TYPE) -> str:
        # we need to transform the ranking schema into a list of table
        table_ranks: t.List[TableRank] = []
        sql = ""

        for element_rank in ranked_schema:
            # first, let's check to see if the new schema is above the token limit
            new_table_sql = self.generate_sql_describe(table_ranks)

            token_count = estimate_token_count(new_table_sql)
            if token_count > self.TOKEN_COUNT_LIMIT:
                log.debug("schema token count", token_count=token_count)
                return sql
            else:
                sql = new_table_sql

            # does the table already exist in table ranks?
            table_rank = next((table_rank for table_rank in table_ranks if table_rank["table_id"] == element_rank["table_id"]), None)

            if not table_rank:
                table_rank = self.create_table_rank(element_rank["table_id"])
                table_ranks.append(table_rank)

            if element_rank["column_id"]:
                column_id = element_rank["column_id"]

                # does the column exist in the table_rank object?
                column_rank = next((column_rank for column_rank in table_rank["columns"] if column_rank["column_id"] == column_id), None)

                if column_rank:
                    # add the hint to the column_rank
                    column_rank["hints"].append(element_rank["value_hint"])
                else:
                    column_rank = self.create_column_rank(element_rank)
                    table_rank["columns"].append(column_rank)

        token_count = estimate_token_count(new_table_sql)
        log.debug("schema token count", token_count=token_count)
        return sql


if __name__ == "__main__":
    from python.utils.connections import Connections

    connections = Connections()
    db = connections.open()

    datasource = db.datasource.find_first(where={"id": 2})

    ranks = Ranker(connections.db, 2).rank("What product sells best in Montana?")

    # generate via: `poetry run python -m python.schema.ranker "What product sells best in Montana?"`

    print(SchemaBuilder(db).build(ranks))
