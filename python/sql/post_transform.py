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
from sqlglot import diff, exp, parse_one
from sqlglot.optimizer import optimize

from python.utils.connections import Connections
from python.utils.logging import log


class PostTransform:
    def __init__(self, datasource_id: int):
        self.connections = Connections()
        self.connections.open()

        self.db = self.connections.db
        self.datasource_id = datasource_id

    def run(self, sql: str):
        ast = parse_one(sql)

        ast = ast.transform(self.cast_divides_to_float)
        ast = ast.transform(self.add_fully_qualified_name)

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

    def add_fully_qualified_name(self, node):
        if isinstance(node, exp.Table):
            # Find the matching table in the db
            print("Node Name: ", node.name)
            db_table = self.db.datasourcetabledescription.find_first(
                where={"dataSourceId": self.datasource_id, "fullyQualifiedName": {"endsWith": f".{node.name.upper()}"}}
            )

            if not db_table:
                log.error("Could not find table in db", table_name=node.name)
                return node

            name_parts = db_table.fullyQualifiedName.split(".")
            wrapped = list(map(lambda x: f'"{x}"', name_parts))
            new_name = ".".join(wrapped)
            return parse_one(new_name)

        return node


# Drop into repl
# code.InteractiveConsole(locals=globals()).interact()

if __name__ == "__main__":
    result = PostTransform(1).run(
        """
    SELECT COUNT(*) FROM orders WHERE shipping_state = 'Montana' AND id IN (SELECT order_id FROM line_items WHERE product_id = (SELECT id FROM products WHERE name = 'Arsenal 2 Pro'))
    """
    )
    print(result)
