"""
The generated SQL is usually postgres form, but at times GPT3 will generate other dialects. We can work with the others
by attempting to parse in other dialects, then converting to snowflake (currently)
"""


import re

from sqlglot import parse_one, transpile
from sqlglot.errors import ParseError

from python.utils.logging import log
from python.utils.openai import is_chat_engine, openai_engine


def _default_in_sql_dialect():
    if is_chat_engine(openai_engine()):
        return "snowflake"

    return "postgres"


class SqlParser:
    # TODO should convert to class params, or just an input into `run`
    in_dialect = _default_in_sql_dialect()
    out_dialect = "snowflake"

    def run(self, sql: str):
        # Some transforms are easier to write in string land for now
        sql = self.string_translations(sql)

        try:
            ast = parse_one(sql, read=self.__class__.in_dialect)
        except ParseError as e:
            log.error("Could not parse SQL, trying tsql", sql=sql, error=e)
            try:
                ast = parse_one(sql, read="tsql")
            except ParseError as e2:
                log.error("Could not parse SQL", sql=sql, error=e2)
                try:
                    ast = parse_one(sql, read="snowflake")
                except ParseError as e3:
                    log.error("Could not parse SQL", sql=sql, error=e3)
                    raise ParseError(f"Could not parse SQL {e3!r}") from e3

        # Convert to output dialect and reparse
        # TODO: there's probably a way to pass in ast and get out ast
        sql = transpile(ast.sql(), read=self.__class__.in_dialect, write=self.__class__.out_dialect)[0]
        ast = parse_one(sql, read=self.__class__.out_dialect)

        return ast

    def string_translations(self, sql):
        # NOW() isn't supported on snowflake, replace with CURRENT_TIMESTAMP()
        sql = re.sub(r"(\s)NOW\(\)", r"\1CURRENT_TIMESTAMP()", sql)

        return sql
