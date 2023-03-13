# Create the schema for a DataSource by querying the embedding indexes and
# deciding which tables, columns, and value hints to include in the prompt.

# always include ID, include ID first, NOT NULL annotations, all `_id` columns on all tables that we include
# order the columns naturally

import re
import typing as t

from python.schema.ranker import SCHEMA_RANKING_TYPE, ElementRank, Ranker
from python.sql.sql_parser import SqlParser
from python.utils.batteries import unique
from python.utils.db import application_database_connection
from python.utils.logging import log
from python.utils.sql import unqualified_table_name
from python.utils.tokens import count_tokens

from prisma import Prisma
from prisma.models import DataSourceTableColumn, DataSourceTableDescription

# from transformers import GPT2Tokenizer


# TODO looks like we cannot set default values on typeddict: https://github.com/python/mypy/issues/6131


class ColumnRank(t.TypedDict):
    column_id: int
    name: str
    hints: t.List[str]


class TableRank(t.TypedDict):
    table_id: int
    fully_qualified_name: str
    columns: t.List[ColumnRank]


TableSchema = t.List[TableRank]


class SchemaBuilder:
    available_tokens: int
    original_available_tokens: int

    def __init__(self, db: Prisma):
        self.db: Prisma = db
        self.cached_columns = {}
        self.cached_table_column_ids = {}
        self.cached_tables: dict[int, DataSourceTableDescription] = {}
        self.tokens_so_far = 0

    def build(self, data_source_id: int, ranked_schema: SCHEMA_RANKING_TYPE, available_tokens: int) -> str:
        # The available tokens is determiend based on the engine and the amount of tokens used for the rest of the
        # prompt
        self.available_tokens = available_tokens
        self.original_available_tokens = available_tokens
        self.cache_columns_and_tables(data_source_id)

        return self.generate_sql_from_element_rank(ranked_schema)

    # Precache all of the tables and columns for faster lookup
    def cache_columns_and_tables(self, data_source_id: int) -> None:
        tables = self.db.datasourcetabledescription.find_many(where={"dataSourceId": data_source_id})

        if len(tables) == 0:
            log.warn("no tables found for data source, cannot cache", data_source_id=data_source_id)

        for table in tables:
            self.cached_tables[table.id] = table

        columns = self.db.datasourcetablecolumn.find_many(where={"dataSourceId": data_source_id})

        for column in columns:
            table_id = column.dataSourceTableDescriptionId
            if table_id not in self.cached_table_column_ids:
                self.cached_table_column_ids[table_id] = []

            column_id = column.id

            self.cached_table_column_ids[table_id].append(column_id)
            self.cached_columns[column_id] = column

    # not caching the columns was creating a massive slowdown in schema generation
    def get_data_source_table_column(self, column_id: int) -> DataSourceTableColumn:
        if column := self.cached_columns.get(column_id, None):
            return column

        if column is None:
            raise ValueError(f"column not found {column_id}")

        return column

    def generate_column_describe(self, column_id: int, hints: t.List[str]) -> str | None:
        # TODO should we filter by kind?
        column = self.get_data_source_table_column(column_id)

        if re.search("^VARCHAR", column.type):
            if SqlParser.in_dialect == "postgres":
                col_type = "VARCHAR"
            else:
                col_type = "TEXT"
        elif re.search("^TIMESTAMP_N?TZ", column.type):
            col_type = "TIMESTAMP"
        elif re.search("^VARIANT", column.type):
            return None  # skip this column
        elif re.search("^NUMBER", column.type):
            if SqlParser.in_dialect == "postgres":
                # NUMBER(38,0) is how int's get encoded in snowflake via fivetran
                col_type = column.type.replace("NUMBER(38,0)", "INTEGER")
                col_type = col_type.replace("NUMBER", "NUMERIC")
            elif SqlParser.in_dialect == "snowflake":
                col_type = column.type.replace("NUMBER(38,0)", "NUMBER")
            else:
                # Don't replace it if it's snowflake
                col_type = column.type
        else:
            col_type = column.type

        rendered_choices = ""

        # remove Nones, empty string, duplicates, and whitespace string from hints
        # NOTE: don't lowercase or dedup based on case, the case needs to match
        # on where clauses
        filtered_hints = [hint for hint in hints if hint and hint.strip()]
        filtered_hints = unique(filtered_hints)

        if filtered_hints:
            # Limit the max value hints to 5
            filtered_hints = filtered_hints[:5]
            raw_choice_list = repr(filtered_hints)
            # cut out the brackets in the repr render
            rendered_choice_list = raw_choice_list[1:-1]
            rendered_choices = f" -- possible values include: {rendered_choice_list}"

        # `column1 datatype(length) column_contraint,`
        return f" {column.name.lower()} {col_type.lower()},{rendered_choices}"

    def generate_sql_table_describe(self, table_rank: TableRank) -> str:
        column_sql = []

        for column_rank in table_rank["columns"]:
            column_description = self.generate_column_describe(column_rank["column_id"], column_rank["hints"])
            if column_description is not None:
                column_sql.append(column_description)

        rendered_column_sql = "\n".join(column_sql)
        rendered_table_name = unqualified_table_name(table_rank["fully_qualified_name"]).lower()

        return f"CREATE TABLE {rendered_table_name} (\n{rendered_column_sql}\n);\n"

    def generate_sql_describe(self, table_ranks: TableSchema) -> str:
        return "\n".join([self.generate_sql_table_describe(table_rank) for table_rank in table_ranks])

    def create_table_rank(self, table_id: int) -> TableRank:
        table = self.cached_tables[table_id]

        # we want to include the primary key and all foreign keys by default as columns
        id_columns = self.db.datasourcetablecolumn.find_many(
            where={
                "AND": [
                    {"dataSourceTableDescriptionId": table_id},
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
            self.create_column_rank(ElementRank(table_id=table_id, column_id=column.id, value_hint=None, score=0.0))
            for column in id_columns
        ]

        return {
            "fully_qualified_name": table.fullyQualifiedName,
            "table_id": table.id,
            "columns": default_id_columns,
        }

    def create_column_rank(self, column_rank: ElementRank) -> ColumnRank:
        column_id = column_rank.column_id
        if not column_id:
            raise ValueError("column_id is required")
        column = self.get_data_source_table_column(column_id)

        result: ColumnRank = {
            "name": column.name,
            "column_id": column.id,
            "hints": [],
        }

        value_hint = column_rank.value_hint

        self.add_hint(result, value_hint)

        return result

    def add_tokens(self, token_str: str, add_extra: int = 0):
        # Add to the count based on the number of tokens in the string,
        # add_extra is used to add in counts for things like line breaks
        count = count_tokens(token_str)
        self.tokens_so_far += count + add_extra

    def generate_sql_from_element_rank(self, ranked_schema: SCHEMA_RANKING_TYPE) -> str:
        # we need to transform the ranking schema into a list of table
        table_ranks: t.List[TableRank] = []
        sql = ""

        for element_rank in ranked_schema:
            if self.tokens_so_far > self.available_tokens:
                log.debug("Passed available token limit")
                break

            # does the table already exist in table ranks?
            table_rank = next(
                (table_rank for table_rank in table_ranks if table_rank["table_id"] == element_rank.table_id), None
            )

            if not table_rank:
                table_id = element_rank.table_id
                table_rank = self.create_table_rank(element_rank.table_id)
                table_ranks.insert(0, table_rank)
                self.add_tokens(
                    f"CREATE TABLE {unqualified_table_name(self.cached_tables[table_id].fullyQualifiedName).lower()} (\n \n);\n"
                )

                # Option to add all columns as soon as we see the table
                # column_ids_for_table = self.cached_table_column_ids[table_id]
                # for column_id in column_ids_for_table:
                #     column_rank = self.add_column_to_table(
                #         ElementRank(table_id=table_id, column_id=column_id, value_hint=None, score=0.0), table_rank
                #     )

            if element_rank.column_id:

                column_id = element_rank.column_id

                # does the column exist in the table_rank object?
                column_rank = next(
                    (column_rank for column_rank in table_rank["columns"] if column_rank["column_id"] == column_id),
                    None,
                )

                if column_rank:
                    # add the hint to the column_rank
                    value_hint = element_rank.value_hint
                    self.add_hint(column_rank, value_hint)
                else:
                    self.add_column_to_table(element_rank, table_rank)
                    if self.tokens_so_far > self.available_tokens:
                        log.debug("Passed available token limit")
                        break

        sql = self.generate_sql_describe(table_ranks)
        token_count = count_tokens(sql)
        log.debug("schema token count", token_count=token_count, available=self.original_available_tokens)
        return sql

    def add_hint(self, column_rank: ColumnRank, value_hint: str | None):
        if value_hint:
            if value_hint and value_hint not in column_rank["hints"]:
                if len(column_rank["hints"]) == 0:
                    self.add_tokens(f" -- possible values include: {value_hint!r}")
                elif len(column_rank["hints"]) < 6:
                    self.add_tokens(f", {value_hint!r}")

                if self.tokens_so_far > self.available_tokens:
                    log.debug("Passed available token limit")

                if len(column_rank["hints"]) < 6:
                    column_rank["hints"].append(value_hint)

    def add_column_to_table(self, element_rank, table_rank):
        column_rank = self.create_column_rank(element_rank)
        table_rank["columns"].append(column_rank)

        # Add the tokens for the column strings without the hints
        column_sql = self.generate_column_describe(column_rank["column_id"], [])
        if column_sql:
            self.add_tokens(column_sql, 2)


if __name__ == "__main__":
    _db = application_database_connection()
    datasource = _db.datasource.find_first(where={"id": 2})

    if datasource:
        ranks = Ranker(2).rank("What product sells best in Montana?")

        # generate via: `poetry run python -m python.schema.ranker "What product sells best in Montana?"`

        print(SchemaBuilder(_db).build(datasource.id, ranks, 7000))
