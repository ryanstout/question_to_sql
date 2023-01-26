# Hanles all of the transforms that need to happen after a query is generated
# from openAI to get it to be useful for the user.
#


import code
import sys

from prisma.models import (
    Business,
    DataSource,
    DataSourceTableColumn,
    DataSourceTableDescription,
    User,
)
from sqlglot import diff, exp, parse_one, transpile
from sqlglot.optimizer import optimize

from python.utils.connections import Connections
from python.utils.logging import log

SNOWFLAKE_KEYWORDS = [
    "ACCOUNT",
    "ALTER",
    "ANY",
    "BY",
    "CASE",
    "CHECK",
    "CONNECT",
    "CONSTRAINT",
    "CROSS",
    "CURRENT_DATE",
    "CURRENT_TIMESTAMP",
    "DELETE",
    "DROP",
    "ELSE",
    "FOLLOWING",
    "FROM",
    "GROUP",
    "IN",
    "INNER",
    "INTERSECT",
    "IS",
    "LEFT",
    "LOCALTIME",
    "NOT",
    "ON",
    "ORDER",
    "REVOKE",
    "RLIKE",
    "ROWS",
    "SAMPLE",
    "SELECT",
    "SOME",
    "TABLESAMPLE",
    "TO",
    "TRUE",
    "UNIQUE",
    "USING",
    "VALUES",
    "WHENEVER",
    "WITH",
]


class PostTransform:
    def __init__(self, datasource_id: int):
        self.connections = Connections()
        self.connections.open()

        self.db = self.connections.db
        self.datasource_id = datasource_id

        self.in_dialect = "postgres"
        self.out_dialect = "snowflake"

    def run(self, sql: str):
        ast = parse_one(sql, self.in_dialect)

        ast = ast.transform(self.cast_divides_to_float)
        ast = ast.transform(self.add_fully_qualified_name)

        sql = transpile(ast.sql(), read=self.in_dialect, write=self.out_dialect)[0]
        print("SQL1: ", sql)
        ast = parse_one(sql, self.out_dialect)
        return ast.sql(pretty=True, max_text_width=40)

    def cast_divides_to_float(self, node):
        # print(type(node))
        if isinstance(node, exp.Div):
            # code.InteractiveConsole(locals=locals()).interact()
            # Need to cast one side on div's to float for postgres
            # Useful for "what percent" questions
            expr = node.args["this"]

            if isinstance(node, exp.TableAlias):
                # Transform the contents of the AS node
                # code.InteractiveConsole(locals=locals()).interact()
                return node
            else:
                node.args["this"] = parse_one(f"{str(expr)}::float")
                return node
        return node

    def quote_if_keyword(self, name: str):
        if name in SNOWFLAKE_KEYWORDS:
            return f'"{name}"'
        else:
            return name

    def add_fully_qualified_name(self, node):
        if isinstance(node, exp.Table) or isinstance(node, exp.Identifier):
            # Find the matching table in the db
            db_table = self.db.datasourcetabledescription.find_first(
                where={"dataSourceId": self.datasource_id, "fullyQualifiedName": {"endsWith": f".{node.name.upper()}"}}
            )

            if not db_table:
                log.error("Could not find table in db", table_name=node.name)
                return node

            name_parts = db_table.fullyQualifiedName.split(".")
            wrapped = list(map(lambda x: self.quote_if_keyword(x), name_parts))
            new_name = ".".join(wrapped)
            return parse_one(new_name, self.in_dialect)

        return node


# Drop into repl
# code.InteractiveConsole(locals=globals()).interact()

if __name__ == "__main__":
    # result = PostTransform(1).run(
    #     """
    # SELECT COUNT(*) FROM orders WHERE shipping_state = 'Montana' AND id IN (SELECT order_id FROM line_items WHERE product_id = (SELECT id FROM products WHERE name = 'Arsenal 2 Pro'))
    # """
    # )

    #     result = PostTransform(1).run(
    #         """
    #     SELECT TOP 1
    #         PRODUCT.TITLE,
    #         COUNT(*) AS SALES
    # FROM
    #         ORDER_LINE
    #         INNER JOIN ORDER ON ORDER_LINE.ORDER_ID = ORDER.ID
    #         INNER JOIN PRODUCT ON ORDER_LINE.PRODUCT_ID = PRODUCT.ID
    # WHERE
    #         ORDER.BILLING_ADDRESS_PROVINCE = 'Montana'
    # GROUP BY
    #         PRODUCT.TITLE
    # ORDER BY
    #         SALES DESC;
    #     """
    #     )
    #     print(result)

    #     result = PostTransform(1).run(
    #         """
    #     SELECT PRODUCT.TITLE, SUM(ORDER_LINE.QUANTITY) AS QUANTITY
    # FROM ORDER_LINE
    # JOIN ORDER ON ORDER_LINE.ORDER_ID = ORDER.ID
    # JOIN PRODUCT ON ORDER_LINE.PRODUCT_ID = PRODUCT.ID
    # WHERE ORDER.BILLING_ADDRESS_PROVINCE = 'Montana'
    # GROUP BY PRODUCT.TITLE
    # ORDER BY QUANTITY DESC
    # LIMIT 1;
    #     """
    #     )
    #     print(result)

    result = PostTransform(1).run(
        """
    
    SELECT TOP 10
        PRODUCT.TITLE,
        PRODUCT.VENDOR,
        PRODUCT.HANDLE,
        PRODUCT.PRODUCT_TYPE,
        PRODUCT.STATUS,
        PRODUCT.

    """
    )
    print(result)
