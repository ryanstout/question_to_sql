# Hanles all of the transforms that need to happen after a query is generated
# from openAI to get it to be useful for the user.
#


from python.setup import log

import re

import utils
from sqlglot import diff, exp, parse_one, transpile
from sqlglot.errors import ParseError
from sqlglot.optimizer import optimize

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
    in_dialect = "postgres"
    # in_dialect = "tsql"
    # in_dialect = "snowflake"
    out_dialect = "snowflake"

    def __init__(self, datasource_id: int):
        self.db = utils.db.application_database_connection()
        self.datasource_id = datasource_id

    def run(self, sql: str):
        # Some transforms are easier to write in string land for now
        sql = self.string_translations(sql)

        # TODO double except here isn't going to do anything...
        try:
            ast = parse_one(sql, self.__class__.in_dialect)
        except ParseError as e:
            log.error("Could not parse SQL, trying tsql", sql=sql, error=e)
            ast = parse_one(sql, "tsql")
        except ParseError as e:
            log.error("Could not parse SQL, trying snowflake", sql=sql, error=e)
            ast = parse_one(sql, "snowflake")

        sql = transpile(ast.sql(), read=self.__class__.in_dialect, write=self.__class__.out_dialect)[0]
        ast = parse_one(sql, self.__class__.out_dialect)

        ast = ast.transform(self.cast_divides_to_float)
        ast = ast.transform(self.add_fully_qualified_name)

        sql = ast.sql(pretty=True, max_text_width=40)

        # Regex transforms

        return sql

    def string_translations(self, sql):
        # NOW() isn't supported on snowflake, replace with CURRENT_TIMESTAMP()
        sql = re.sub(r"(\s)NOW\(\)([\s,;\n])", r"\1CURRENT_TIMESTAMP()\1", sql)

        return sql

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
                log.debug("Could not find table in db", table_name=node.name)
                return node

            # FQN everything
            if False:
                name_parts = db_table.fullyQualifiedName.split(".")
                wrapped = list(map(lambda x: self.quote_if_keyword(x), name_parts))
                new_name = ".".join(wrapped)
            else:
                new_name = self.quote_if_keyword(db_table.fullyQualifiedName.split(".")[-1])
            return parse_one(new_name, self.__class__.in_dialect)

        return node


# Drop into repl
# code.InteractiveConsole(locals=globals()).interact()

if __name__ == "__main__":
    # result = PostTransform(1).run(
    #     """
    # SELECT COUNT(*) FROM orders WHERE shipping_state = 'Montana' AND id IN (SELECT order_id FROM line_items WHERE product_id = (SELECT id FROM products WHERE name = 'Arsenal 2 Pro'))
    # """
    # )

    # result = PostTransform(1).run(
    #     """
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
    # )
    # print(result)

    # result = PostTransform(1).run(
    #     """
    #     SELECT PRODUCT.TITLE, SUM(ORDER_LINE.QUANTITY) AS QUANTITY
    # FROM ORDER_LINE
    # JOIN ORDER ON ORDER_LINE.ORDER_ID = ORDER.ID
    # JOIN PRODUCT ON ORDER_LINE.PRODUCT_ID = PRODUCT.ID
    # WHERE ORDER.BILLING_ADDRESS_PROVINCE = 'Montana'
    # GROUP BY PRODUCT.TITLE
    # ORDER BY QUANTITY DESC
    # LIMIT 1;
    #     """
    # )
    # print(result)

    # result = PostTransform(1).run(
    #     """
    #     SELECT
    #         COUNT(*)
    #     FROM "ORDER"
    #     WHERE
    #         customer_id = (
    #             SELECT
    #             id
    #             FROM CUSTOMER
    #             WHERE
    #             first_name = 'Daniel'
    #             AND last_name = 'Whitehouse' LIMIT 1
    #         )
    #     """
    # )
    # print(result)

    result = PostTransform(1).run(
        """
    SELECT TOP 10 COUNT(*) AS orders_per_product,
  PRODUCT.title
FROM "ORDER"
JOIN ORDER_LINE
  ON ORDER_LINE.order_id = "ORDER".id
JOIN PRODUCT_VARIANT
  ON PRODUCT_VARIANT.id = ORDER_LINE.variant_id
JOIN PRODUCT
  ON PRODUCT.id = PRODUCT_VARIANT.product_id
GROUP BY
  PRODUCT.title
ORDER BY
orders_per_product DESC NULLS FIRST;
"""
    )
    print(result)
